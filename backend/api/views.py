import os
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
        master_resume_id = request.data.get('master_resume_id')
        job_description_id = request.data.get('job_description_id')
        
        try:
            master_resume = MasterResume.objects.get(id=master_resume_id)
            job_description = JobDescription.objects.get(id=job_description_id)
        except MasterResume.DoesNotExist:
            return Response({'error': 'Master resume not found'}, status=status.HTTP_404_NOT_FOUND)
        except JobDescription.DoesNotExist:
            return Response({'error': 'Job description not found'}, status=status.HTTP_404_NOT_FOUND)

        # Extract text from PDF files
        master_resume_text = self.extract_text_from_pdf(master_resume.resume_file.path)
        job_description_text = self.extract_text_from_pdf(job_description.description_file.path)

        # AI-powered customization logic
        customized_content = self.ai_customize(master_resume_text, job_description_text)

        # Create a new PDF from the customized content
        customized_resume_path = self.create_pdf_from_text(customized_content)

        # Save the customized resume to the database
        with open(customized_resume_path, 'rb') as f:
            customized_resume_file = ContentFile(f.read())
            customized_resume = CustomizedResume.objects.create(
                user=request.user,
                master_resume=master_resume,
                job_description=job_description,
                customized_resume_file=customized_resume_file
            )

        serializer = self.get_serializer(customized_resume)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def extract_text_from_pdf(self, pdf_path):
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

    def ai_customize(self, master_resume_text, job_description_text):
        # Use Google Gemini AI to customize the resume
        client = genai.Client(api_key=GEMINI_AI_KEY)
        prompt = f"Customize the following resume text based on the job description provided:\n\nResume:\n{master_resume_text}\n\nJob Description:\n{job_description_text}"
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents=prompt
        )
        
        # Extract the customized content from the response
        customized_content = response['choices'][0]['text']
        return customized_content

    def create_pdf_from_text(self, text):
        writer = PdfWriter()
        writer.add_page(writer.add_blank_page(width=210, height=297))  # A4 size
        writer.pages[0].insert_text(text)
        customized_resume_path = os.path.join(settings.MEDIA_ROOT, 'customized_resumes', 'customized_resume.pdf')
        with open(customized_resume_path, 'wb') as f:
            writer.write(f)
        return customized_resume_path