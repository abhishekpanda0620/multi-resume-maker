import os
import uuid
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ValidationError

from ..models import MasterResume, JobDescription, CustomizedResume
from ..utils.pdf_processor import PDFProcessor
from ..utils.ai_service import AIService

logger = logging.getLogger('resume_customizer')

class ResumeCustomizer:
    """Service class for customizing resumes based on job descriptions"""
    
    def __init__(self, user):
        self.user = user
        self.pdf_processor = PDFProcessor()
        self.ai_service = AIService()
        self.temp_files = []
    
    def customize_resume(self, master_resume_file, job_description):
        """Main method to customize a resume"""
        try:
            # Validate input
            if not master_resume_file:
                logger.error("No resume file provided")
                raise ValidationError("No resume file provided")
            if not job_description:
                logger.error("No job description provided")
                raise ValidationError("No job description provided")
            
            # Save temporary file
            temp_path = default_storage.save(f'temp/{uuid.uuid4()}_{master_resume_file.name}', master_resume_file)
            temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_path)
            self.temp_files.append(temp_file_path)
            logger.info(f"Temporary file saved: {temp_file_path}")
            
            # Extract text with layout and block info
            layout_info, text_blocks = self.pdf_processor.extract_text_with_layout(temp_file_path)
            if not layout_info:
                raise ValidationError("No text extracted from PDF")
            logger.info(f"Extracted {len(layout_info)} text items with layout")
            logger.info(f"Text blocks map has {len(text_blocks)} entries")
            
            # Identify sections
            sections = self.pdf_processor.identify_sections(layout_info)
            logger.info(f"Identified sections: {list(sections.keys())}")
            
            # Generate replacements
            replacements = self._generate_replacements(sections, job_description, text_blocks)
            logger.info(f"Generated {len(replacements)} replacements")
            
            # Replace text in PDF
            customized_resume_path = self.pdf_processor.replace_text_in_pdf(temp_file_path, replacements)
            self.temp_files.append(customized_resume_path)
            logger.info(f"Customized PDF created: {customized_resume_path}")
            
            # Save to database
            return self._save_to_database(master_resume_file, job_description, customized_resume_path)
            
        finally:
            self._cleanup_temp_files()
    
    def _generate_replacements(self, sections, job_description, text_blocks):
        """Generate text replacements with improved text block matching"""
        replacements = {}
        
        # Process each section separately
        for section_name, items in sections.items():
            if not items:
                continue
            
            # Extract original text content for this section
            # Group items by their proximity to improve context
            groups = self._group_items_by_proximity(items)
            
            for group in groups:
                # Extract text from this group
                original_texts = [item['text'].strip() for item in group]
                original_text_full = '\n'.join(original_texts)
                
                if len(original_text_full) < 10:  # Skip very short sections
                    continue
                
                # Get AI-generated customized content for this group
                customized_text = self.ai_service.generate_customized_content(
                    original_text_full, 
                    job_description,
                    section_name
                )
                
                logger.info(f"Original group in '{section_name}' length: {len(original_text_full)}")
                logger.info(f"Customized group in '{section_name}' length: {len(customized_text)}")
                
                # Create better matching chunks
                customized_chunks = self._create_matching_chunks(original_texts, customized_text)
                
                # Match text blocks for replacement
                for i, (orig_text, new_text) in enumerate(zip(original_texts, customized_chunks)):
                    if not orig_text.strip() or not new_text.strip():
                        continue
                    
                    # Find the best matching block
                    matched_key = self._find_best_matching_block(orig_text, text_blocks)
                    
                    if matched_key:
                        # Store replacement with additional info
                        replacements[matched_key] = {
                            'text': new_text,
                            'info': text_blocks[matched_key]
                        }
                        logger.info(f"Created replacement in {section_name}: '{orig_text[:30]}...' -> '{new_text[:30]}...'")
            
        return replacements
    
    def _group_items_by_proximity(self, items):
        """Group items by their vertical proximity to capture related content"""
        if not items:
            return []
            
        # Sort items by Y position
        sorted_items = sorted(items, key=lambda x: x['bbox'][1])
        
        groups = []
        current_group = [sorted_items[0]]
        
        for i in range(1, len(sorted_items)):
            current_item = sorted_items[i]
            prev_item = sorted_items[i-1]
            
            # Calculate vertical distance
            vertical_gap = current_item['bbox'][1] - prev_item['bbox'][3]
            
            # If gap is small, add to current group
            if vertical_gap < 20:  # Threshold in points
                current_group.append(current_item)
            else:
                # Start a new group
                groups.append(current_group)
                current_group = [current_item]
        
        # Add the last group
        if current_group:
            groups.append(current_group)
            
        return groups
    
    def _create_matching_chunks(self, original_texts, customized_text):
        """Create customized text chunks that better match original text structure"""
        # Count total content length in original and customized text
        orig_chars_total = sum(len(text) for text in original_texts)
        custom_chars_total = len(customized_text)
        
        # Calculate proportions and split intelligently
        chunks = []
        start_pos = 0
        
        for orig_text in original_texts:
            orig_length = len(orig_text)
            # Calculate proportional chunk size
            proportion = orig_length / max(1, orig_chars_total)
            chunk_size = max(1, int(proportion * custom_chars_total))
            
            # Adjust to sentence or punctuation boundaries where possible
            end_pos = min(start_pos + chunk_size, custom_chars_total)
            
            # Look for sentence-ending punctuation near the calculated end position
            window_size = min(30, chunk_size // 2)  # Look 30 chars or half chunk size, whichever is smaller
            search_start = max(start_pos, end_pos - window_size)
            search_end = min(custom_chars_total, end_pos + window_size)
            
            # Find the nearest sentence break
            sentence_break = end_pos
            for i in range(end_pos, search_start, -1):
                if i < custom_chars_total and customized_text[i-1] in '.!?':
                    sentence_break = i
                    break
            
            # If no sentence break found going backward, try forward
            if sentence_break == end_pos:
                for i in range(end_pos, search_end):
                    if i < custom_chars_total and customized_text[i-1] in '.!?':
                        sentence_break = i
                        break
            
            # Extract the chunk
            chunk = customized_text[start_pos:sentence_break].strip()
            chunks.append(chunk)
            start_pos = sentence_break
        
        # If we have remaining text, add it to the last chunk
        if start_pos < custom_chars_total and chunks:
            chunks[-1] = chunks[-1] + ' ' + customized_text[start_pos:].strip()
        
        # Ensure we have the same number of chunks as original texts
        while len(chunks) < len(original_texts):
            chunks.append("")
            
        return chunks[:len(original_texts)]
    
    def _find_best_matching_block(self, text, text_blocks):
        """Find the best matching text block for replacement"""
        best_match = None
        best_score = 0
        
        for key, block_info in text_blocks.items():
            block_text = block_info.get('text', '')
            
            # Calculate match score based on content overlap
            if text == block_text:
                # Exact match
                return key
            elif text in block_text:
                # Text is substring of block
                score = len(text) / len(block_text)
                if score > best_score:
                    best_score = score
                    best_match = key
            elif block_text in text:
                # Block is substring of text
                score = len(block_text) / len(text)
                if score > best_score:
                    best_score = score
                    best_match = key
        
        # Return best match if score is good enough
        if best_score > 0.5:  # Threshold for good match
            return best_match
        return None
    
    def _save_to_database(self, master_resume_file, job_description, customized_resume_path):
        """Save customized resume to database"""
        try:
            master_resume = MasterResume.objects.create(
                resume_file=master_resume_file, 
                user=self.user
            )
            job_description_obj = JobDescription.objects.create(
                description_text=job_description, 
                user=self.user
            )
            
            with open(customized_resume_path, 'rb') as f:
                customized_resume_file = ContentFile(f.read())
                filename = f'customized_resume_{uuid.uuid4()}.pdf'
                customized_resume = CustomizedResume.objects.create(
                    master_resume=master_resume,
                    job_description=job_description_obj,
                    user=self.user
                )
                customized_resume.customized_resume_file.save(filename, customized_resume_file)
            
            logger.info(f"Customized resume saved with ID: {customized_resume.id}")
            return customized_resume
            
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}", exc_info=True)
            raise ValidationError(f"Error saving customized resume: {str(e)}")
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.info(f"Cleaned up: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {str(e)}")