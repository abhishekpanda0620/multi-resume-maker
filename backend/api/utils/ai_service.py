import logging
from django.conf import settings
from django.core.exceptions import ValidationError
import json
from google import genai

logger = logging.getLogger('resume_customizer')

class AIService:
    """Service class for AI-related functionality"""
    
    def __init__(self):
        try:
            self.client = genai.Client(api_key=settings.GEMINI_AI_KEY)
            # self.model = self.client.models.get("gemini-1.5-pro")
        except Exception as e:
            logger.error(f"Error initializing Gemini client: {str(e)}", exc_info=True)
            raise ValidationError(f"Error initializing AI service: {str(e)}")
    
    def generate_customized_content(self, original_text, job_description, section_name=""):
        """Generate customized content using Google Gemini AI with improved instructions"""
        try:
            # Create a more specific prompt based on section
            prompt = self._create_section_specific_prompt(original_text, job_description, section_name)
            
            # Configure generation parameters
            # generation_config = {
            #     "temperature": 0.1,  # Lower temperature for more focused output
            #     "top_p": 0.95,
            #     "top_k": 40,
            #     "max_output_tokens": 8192,
            # }
            
            # # Add safety settings as needed
            # safety_settings = {
            #     "HARASSMENT": "BLOCK_NONE",
            #     "HATE": "BLOCK_NONE",
            #     "SEXUAL": "BLOCK_NONE",
            #     "DANGEROUS": "BLOCK_NONE",
            # }
            
            # Generate content
            response = self.client.models.generate_content(
                contents=prompt,
                model='gemini-1.5-pro',    
            )
            
            # Process and return the text
            new_text = response.text.strip()
            logger.debug(f"AI generated text length: {len(new_text)} characters")
            
            # Ensure we're not getting something drastically different in length
            if len(new_text) < len(original_text) * 0.5 or len(new_text) > len(original_text) * 1.5:
                logger.warning(f"AI generated text length ({len(new_text)}) differs substantially from original ({len(original_text)})")
                # Try to adjust the text length if needed
                new_text = self._adjust_text_length(new_text, original_text)
            
            return new_text
            
        except Exception as e:
            logger.error(f"Error generating AI content: {str(e)}", exc_info=True)
            # Fallback to original text in case of errors
            return original_text
    
    def _create_section_specific_prompt(self, original_text, job_description, section_name):
        """Create a section-specific prompt for better customization"""
        # Base instructions for all sections
        instructions = [
            "Maintain the original structure and formatting",
            "Keep approximately the same length as the original text",
            "Use professional language consistent with the original",
            "Preserve dates, company names, and education details",
            "DO NOT add new sections or completely rewrite the content",
            "Focus on subtle refinements that align with the job description"
        ]
        
        # Add section-specific instructions
        if section_name.lower() == "summary":
            instructions.extend([
                "Emphasize skills and qualities mentioned in the job description",
                "Keep the personal tone and voice consistent with the original"
            ])
        elif section_name.lower() == "experience":
            instructions.extend([
                "Highlight achievements that relate to the job requirements",
                "Use action verbs and quantify results where possible",
                "Maintain chronological order and date formats"
            ])
        elif section_name.lower() == "skills":
            instructions.extend([
                "Prioritize skills mentioned in the job description",
                "Keep technical terms and industry terminology accurate",
                "Maintain the original skill categorization if present"
            ])
        elif section_name.lower() == "education":
            instructions.extend([
                "Keep all educational qualifications exactly as in the original",
                "Only make minor wording changes if necessary"
            ])
        
        # Construct the full prompt
        return f"""
        You are a professional resume customization expert. Tailor this {section_name} section to better match the job description while preserving the original format and style.

        JOB DESCRIPTION:
        {job_description}

        ORIGINAL {section_name.upper()} SECTION:
        {original_text}
        
        INSTRUCTIONS:
        {' '.join(['- ' + instr for instr in instructions])}
        
        IMPORTANT: Maintain exactly the same text length and structure as the original. Focus on subtle keyword optimization without changing the overall format.
        
        CUSTOMIZED {section_name.upper()} SECTION:
        """
    
    def _adjust_text_length(self, new_text, original_text):
        """Adjust the length of the generated text to match the original"""
        original_length = len(original_text)
        new_length = len(new_text)
        
        # If the text is too short, try to expand it
        if new_length < original_length * 0.8:
            logger.info(f"Generated text too short, attempting to expand")
            try:
                expansion_prompt = f"""
                The following text needs to be expanded to approximately {original_length} characters 
                while maintaining the same meaning and professional tone. Please expand:
                
                {new_text}
                """
                
                expansion_response =self.client.models.generate_content(
                contents=expansion_prompt,
                model='gemini-1.5-pro',
            )
                expanded_text = expansion_response.text.strip()
                
                # Check if expansion was successful
                if len(expanded_text) > new_length:
                    return expanded_text
            except Exception as e:
                logger.warning(f"Failed to expand text: {str(e)}")
        
        # If the text is too long, try to shorten it
        elif new_length > original_length * 1.2:
            logger.info(f"Generated text too long, attempting to shorten")
            try:
                shortening_prompt = f"""
                The following text needs to be shortened to approximately {original_length} characters
                while maintaining the professional tone and all key information. Please condense:
                
                {new_text}
                """
                
                shortening_response = response = self.client.models.generate_content(
                contents=shortening_prompt,
                model='gemini-1.5-pro',
            )
                shortened_text = shortening_response.text.strip()
                
                # Check if shortening was successful
                if len(shortened_text) < new_length:
                    return shortened_text
            except Exception as e:
                logger.warning(f"Failed to shorten text: {str(e)}")
        
        # Return the original generated text if adjustments failed
        return new_text