import os
import uuid
import logging
import fitz  # PyMuPDF
from django.conf import settings
from django.core.exceptions import ValidationError
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar

logger = logging.getLogger('resume_customizer')

class PDFProcessor:
    """Utility class for PDF processing operations"""
    
    def extract_text_with_layout(self, pdf_path):
        """Extract text with layout and map to raw bytes"""
        layout_info = []
        text_blocks = {}  # Maps text blocks to their positions
        
        try:
            # Use pdfminer for detailed layout info
            for page_layout in extract_pages(pdf_path):
                for element in page_layout:
                    if isinstance(element, LTTextBox):
                        for line in element:
                            if isinstance(line, LTTextLine):
                                text = ''.join(char.get_text() for char in line if isinstance(char, LTChar))
                                if text.strip():
                                    layout_info.append({
                                        'text': text,
                                        'bbox': line.bbox,
                                        'font': line._objs[0].fontname if line._objs else None,
                                        'size': line._objs[0].size if line._objs else None
                                    })
            
            # Use PyMuPDF for text block extraction (more reliable for replacement)
            self._extract_text_blocks(pdf_path, text_blocks)
            
            logger.info(f"Extracted {len(layout_info)} text items with layout")
            logger.info(f"Extracted {len(text_blocks)} text blocks for replacement")
            
            return layout_info, text_blocks
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}", exc_info=True)
            raise ValidationError(f"Error extracting text from PDF: {str(e)}")
    
    def _extract_text_blocks(self, pdf_path, text_blocks):
        """Extract text blocks with PyMuPDF for more reliable replacement"""
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc):
                # Get text blocks with their details
                blocks = page.get_text("dict")["blocks"]
                for b in blocks:
                    if "lines" in b:
                        for line in b["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:
                                    # Use a more unique key to prevent overwrites
                                    key = f"{text}_{page_num}_{span['bbox'][0]:.1f}_{span['bbox'][1]:.1f}"
                                    text_blocks[key] = {
                                        'text': text,
                                        'page': page_num,
                                        'rect': fitz.Rect(span["bbox"]),
                                        'font': span["font"],
                                        'size': span["size"],
                                        'color': span["color"]
                                    }
            doc.close()
        except Exception as e:
            logger.error(f"Error in PyMuPDF text extraction: {e}", exc_info=True)
                
    def identify_sections(self, layout_info):
        """Identify sections in the resume"""
        sections = {'Summary': [], 'Experience': [], 'Skills': [], 'Education': []}
        current_section = None
        
        # Sort layout_info by vertical position (top to bottom)
        sorted_layout = sorted(layout_info, key=lambda x: x['bbox'][1])
        
        for item in sorted_layout:
            text = item['text'].strip().lower()
            font_size = item.get('size', 0)
            
            # Check for section headers - look for larger font sizes and keywords
            is_header = font_size > 11 or (len(text) < 30 and any(c.isupper() for c in item['text']))
            
            if is_header:
                if any(keyword in text for keyword in ['summary', 'profile', 'objective', 'about']):
                    current_section = 'Summary'
                elif any(keyword in text for keyword in ['experience', 'work history', 'employment', 'professional']):
                    current_section = 'Experience'
                elif any(keyword in text for keyword in ['skills', 'competencies', 'abilities', 'expertise']):
                    current_section = 'Skills'
                elif any(keyword in text for keyword in ['education', 'academic', 'degree', 'university']):
                    current_section = 'Education'
            
            # Add item to current section if we have one
            if current_section and text.strip():
                sections[current_section].append(item)
                
        # Return only non-empty sections
        return {k: v for k, v in sections.items() if v}
    
    def replace_text_in_pdf(self, original_pdf_path, replacements):
        """Replace text in the PDF using improved text replacement strategy"""
        try:
            output_path = os.path.join(
                settings.MEDIA_ROOT, 
                'customized_resumes', 
                f'customized_resume_{uuid.uuid4()}.pdf'
            )
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create a copy of the original PDF
            doc = fitz.open(original_pdf_path)
            replaced_count = 0
            
            # Create a map of pages to process with their replacements
            page_replacements = {}
            for key, replacement_info in replacements.items():
                # Skip if missing info
                if 'info' not in replacement_info:
                    continue
                
                # Get original text from info
                original_text = replacement_info['info'].get('text', '')
                if not original_text:
                    continue
                
                page_num = replacement_info['info'].get('page', 0)
                if page_num not in page_replacements:
                    page_replacements[page_num] = []
                    
                page_replacements[page_num].append({
                    'original': original_text,
                    'new_text': replacement_info['text'],
                    'rect': replacement_info['info'].get('rect'),
                    'font': replacement_info['info'].get('font'),
                    'size': replacement_info['info'].get('size'),
                    'color': replacement_info['info'].get('color')
                })
            
            # Process each page with its replacements
            for page_num in sorted(page_replacements.keys()):
                if page_num >= len(doc):
                    logger.warning(f"Page {page_num} doesn't exist in document with {len(doc)} pages")
                    continue
                    
                page = doc[page_num]
                
                # Sort replacements from bottom to top, right to left to avoid overlapping issues
                page_replacements[page_num].sort(
                    key=lambda x: (
                        -x['rect'].y1 if x.get('rect') else 0,  # Bottom to top
                        x['rect'].x0 if x.get('rect') else 0    # Left to right
                    )
                )
                
                for replacement in page_replacements[page_num]:
                    original_text = replacement['original']
                    new_text = replacement['new_text']
                    rect = replacement.get('rect')
                    
                    if not new_text or not original_text or not rect:
                        continue
                    
                    # Create a clean white rectangle slightly larger than the text area
                    padding = 1  # Small padding to ensure complete coverage
                    clean_rect = fitz.Rect(
                        rect.x0 - padding,
                        rect.y0 - padding,
                        rect.x1 + padding,
                        rect.y1 + padding
                    )
                    page.draw_rect(clean_rect, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # Get the best font
                    font_name = self._get_best_font(doc, replacement.get('font', "helv"))
                    font_size = replacement.get('size', 11)
                    
                    # Normalize font size
                    if font_size < 6 or font_size > 24:
                        font_size = 11
                    
                    # Get text color
                    color = self._normalize_color(replacement.get('color', 0))
                    
                    # Calculate vertical adjustment based on font metrics
                    # This is crucial to prevent vertical misalignment
                    vertical_adjustment = font_size * 0.2  # Empirical value that works well
                    
                    # Handle text that might be too wide for the rectangle
                    self._insert_text_with_wrapping(
                        page, 
                        rect, 
                        new_text, 
                        font_name, 
                        font_size, 
                        color, 
                        vertical_adjustment
                    )
                    
                    replaced_count += 1
            
            # Save the modified document
            doc.save(output_path)
            doc.close()
            
            logger.info(f"Replaced {replaced_count} text instances in the PDF")
            return output_path
            
        except Exception as e:
            logger.error(f"Error replacing text in PDF: {str(e)}", exc_info=True)
            raise ValidationError(f"Error customizing PDF: {str(e)}")
    
    def _get_best_font(self, doc, preferred_font=None):
        """Get the best font to use for text replacement"""
        # Standard fonts that should always be available
        standard_fonts = ["helv", "tiro", "cour", "zapf"]
        
        if preferred_font:
            # Clean up font name to match standard patterns
            clean_font = preferred_font.lower().replace('-', '').replace(' ', '')
            
            # Try to map to a standard font
            if "times" in clean_font or "roman" in clean_font:
                return "tiro"  # Times Roman equivalent
            elif "helvetica" in clean_font or "arial" in clean_font:
                return "helv"  # Helvetica/Arial equivalent
            elif "courier" in clean_font or "mono" in clean_font:
                return "cour"  # Courier equivalent
            
        # Default to Helvetica which works well in most cases
        return "helv"
    
    def _normalize_color(self, color):
        """Normalize color to RGB tuple"""
        if isinstance(color, int):
            r = ((color >> 16) & 0xFF) / 255
            g = ((color >> 8) & 0xFF) / 255
            b = (color & 0xFF) / 255
            return (r, g, b)
        elif isinstance(color, (list, tuple)) and len(color) >= 3:
            # Ensure values are between 0 and 1
            return tuple(min(1, max(0, c)) for c in color[:3])
        else:
            return (0, 0, 0)  # Default to black
    
    def _insert_text_with_wrapping(self, page, rect, text, font_name, font_size, color, vertical_adjustment):
        """Insert text with proper wrapping if needed"""
        try:
            # Calculate available width
            available_width = rect.width
            
            # Check if text fits in the available width
            text_width = fitz.get_text_length(text, fontname=font_name, fontsize=font_size)
            
            if text_width <= available_width * 1.05:  # Allow 5% overflow
                # Text fits, insert at original position with vertical adjustment
                insertion_point = (rect.x0, rect.y1 - vertical_adjustment)
                page.insert_text(
                    point=insertion_point,
                    text=text,
                    fontname=font_name,
                    fontsize=font_size,
                    color=color
                )
            else:
                # Text doesn't fit, need to wrap or scale
                if len(text) > 50:  # Longer text: wrap
                    words = text.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        test_line = current_line + [word]
                        test_text = ' '.join(test_line)
                        test_width = fitz.get_text_length(test_text, fontname=font_name, fontsize=font_size)
                        
                        if test_width <= available_width:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(' '.join(current_line))
                                current_line = [word]
                            else:
                                # Word is too long by itself, just add it
                                lines.append(word)
                                current_line = []
                    
                    # Add remaining words
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    # Draw each line
                    line_height = font_size * 1.2
                    max_lines = min(len(lines), max(1, int(rect.height / line_height)))
                    
                    for i in range(max_lines):
                        # Calculate Y position for each line
                        y_pos = rect.y0 + (i + 1) * line_height - vertical_adjustment
                        
                        # Don't go below the bottom of the rectangle
                        if y_pos > rect.y1:
                            break
                            
                        page.insert_text(
                            point=(rect.x0, y_pos),
                            text=lines[i],
                            fontname=font_name,
                            fontsize=font_size,
                            color=color
                        )
                else:
                    # For shorter text, scale down the font size
                    adjusted_size = font_size * (available_width / text_width) * 0.95
                    adjusted_size = max(7, min(adjusted_size, font_size))  # Don't go too small
                    
                    insertion_point = (rect.x0, rect.y1 - vertical_adjustment * (adjusted_size/font_size))
                    page.insert_text(
                        point=insertion_point,
                        text=text,
                        fontname=font_name,
                        fontsize=adjusted_size,
                        color=color
                    )
        
        except Exception as e:
            logger.warning(f"Error inserting text: {str(e)}")
            # Fallback with absolute minimum parameters
            try:
                page.insert_text(
                    point=(rect.x0, rect.y1 - 10), 
                    text=text[:50] + ("..." if len(text) > 50 else ""),  # Truncate if very long
                    fontname="helv",
                    fontsize=9,
                    color=(0, 0, 0)
                )
            except Exception as fallback_error:
                logger.error(f"Fallback text insertion failed: {str(fallback_error)}")