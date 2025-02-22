import os
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from PyPDF2 import PdfReader, PdfWriter
from .models import MasterResume, JobDescription, CustomizedResume
from .serializers import MasterResumeSerializer, JobDescriptionSerializer, CustomizedResumeSerializer
from google import genai


class MasterResumeViewSet(viewsets.ModelViewSet):
    queryset = MasterResume.objects.all()
    serializer_class = MasterResumeSerializer

class JobDescriptionViewSet(viewsets.ModelViewSet):
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer

class CustomizedResumeViewSet(viewsets.ModelViewSet):
    queryset = CustomizedResume.objects.all()
    serializer_class = CustomizedResumeSerializer

    @action(detail=False, methods=['post'])
    def customize(self, request):
        try:
            # Get the uploaded file and job description from request
            master_resume_file = request.FILES.get('master_resume')
            job_description = request.data.get('job_description')

            if not master_resume_file:
                return Response(
                    {'error': 'No resume file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not job_description:
                return Response(
                    {'error': 'No job description provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save the master resume temporarily
            temp_path = default_storage.save(
                f'temp/{master_resume_file.name}',
                master_resume_file
            )
            temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_path)

            # Extract text from PDF file
            master_resume_text = self.extract_text_from_pdf(temp_file_path)

            # AI-powered customization logic
            customized_content = self.ai_customize(master_resume_text, job_description)

            # Create a new PDF from the customized content
            customized_resume_path = self.create_pdf_from_text(customized_content)

            # Create a new master resume record
            master_resume = MasterResume.objects.create(
                resume_file=master_resume_file
            )

            # Create a new job description record
            job_description_obj = JobDescription.objects.create(
                description_text=job_description
            )

            # Save the customized resume to the database
            with open(customized_resume_path, 'rb') as f:
                customized_resume_file = ContentFile(f.read())
                filename = f'customized_resume_{master_resume.id}.pdf'
                customized_resume = CustomizedResume.objects.create(
                    master_resume=master_resume,
                    job_description=job_description_obj
                )
                customized_resume.customized_resume_file.save(
                    filename, 
                    customized_resume_file
                )

            # Clean up temporary files
            os.remove(temp_file_path)
            os.remove(customized_resume_path)

            return Response({
                'customized_resume_file': customized_resume.customized_resume_file.url,
                'message': 'Resume customized successfully'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def extract_text_from_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def ai_customize(self, master_resume_text, job_description_text):
        try:
            # Use Google Gemini AI to customize the resume
            client = genai.Client(api_key=settings.GEMINI_AI_KEY)
            prompt = f"""
            You are a professional resume customizer. Your task is to customize the following resume 
            to match the job description provided. Keep the formatting and structure similar but 
            optimize the content to highlight relevant skills and experiences.

            Resume:
            {master_resume_text}

            Job Description:
            {job_description_text}

            Please provide the customized resume content maintaining a professional format.
            """
            
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt
            )
            
            if not response or not response.text:
                raise Exception("Failed to generate customized content")

            return response.text
            
        except Exception as e:
            raise Exception(f"Error in AI customization: {str(e)}")

    def create_pdf_from_text(self, text):
        try:
            writer = PdfWriter()
            writer.add_page(writer.add_blank_page(width=612, height=792))  # US Letter size
            
            # Create a unique filename
            filename = f'customized_resume_{uuid.uuid4()}.pdf'
            output_path = os.path.join(settings.MEDIA_ROOT, 'customized_resumes', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write content to PDF
            writer.pages[0].insert_text(
                text=text,
                x=50,  # Left margin
                y=750,  # Top margin
                font_size=12
            )
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Error creating PDF: {str(e)}")