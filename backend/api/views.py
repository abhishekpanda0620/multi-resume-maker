import os
import uuid
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from PyPDF2 import PdfReader, PdfWriter
from .models import MasterResume, JobDescription, CustomizedResume
from .serializers import MasterResumeSerializer, JobDescriptionSerializer, CustomizedResumeSerializer, UserSerializer, RegisterSerializer
from google import genai
from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

import textwrap

logger = logging.getLogger('resume_customizer')

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()  # This returns the User instance

        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Prepare the response data
        user_data = serializer.data
        token_data = {
            'accessToken': access_token,
            'refreshToken': str(refresh)
        }
        response_data = {**user_data, **token_data}

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class UserView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
class MasterResumeViewSet(viewsets.ModelViewSet):
    queryset = MasterResume.objects.all()
    serializer_class = MasterResumeSerializer

class JobDescriptionViewSet(viewsets.ModelViewSet):
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer

class CustomizedResumeViewSet(viewsets.ModelViewSet):
    queryset = CustomizedResume.objects.all()
    serializer_class = CustomizedResumeSerializer
    permission_classes = [IsAuthenticated]
    @action(detail=False, methods=['post'])
    def customize(self, request):
        logger.info(f"Starting resume customization process for user: {request.user}")
        temp_files = []
         # If the user is not authenticated (shouldn't happen due to permissions), you could check:
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # Validate input
            master_resume_file = request.FILES.get('master_resume')
            job_description = request.data.get('job_description')

            if not master_resume_file:
                logger.error("No resume file provided in request")
                return Response(
                    {'error': 'No resume file provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not job_description:
                logger.error("No job description provided in request")
                return Response(
                    {'error': 'No job description provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Save the master resume temporarily
            try:
                temp_path = default_storage.save(
                    f'temp/{master_resume_file.name}',
                    master_resume_file
                )
                temp_file_path = os.path.join(settings.MEDIA_ROOT, temp_path)
                temp_files.append(temp_file_path)
                logger.info(f"Temporary file saved: {temp_file_path}")
            except Exception as e:
                logger.error(f"Error saving temporary file: {str(e)}")
                raise ValidationError(f"Error saving resume file: {str(e)}")

            # Extract text from PDF file
            try:
                master_resume_text = self.extract_text_from_pdf(temp_file_path)
                logger.info("Successfully extracted text from PDF")
            except Exception as e:
                logger.error(f"Error extracting text from PDF: {str(e)}")
                raise ValidationError(f"Error reading PDF file: {str(e)}")

            # AI-powered customization logic
            try:
                customized_content = self.ai_customize(master_resume_text, job_description)
                logger.info("Successfully customized resume content")
            except Exception as e:
                logger.error(f"Error in AI customization: {str(e)}")
                raise ValidationError(f"Error customizing resume: {str(e)}")

            # Create a new PDF from the customized content
            try:
                customized_resume_path = self.create_pdf_from_text(customized_content)
                temp_files.append(customized_resume_path)
                logger.info(f"Created customized PDF: {customized_resume_path}")
            except Exception as e:
                logger.error(f"Error creating PDF: {str(e)}")
                raise ValidationError(f"Error creating customized PDF: {str(e)}")

            # Save to database
            try:
                master_resume = MasterResume.objects.create(resume_file=master_resume_file,user = request.user)
                job_description_obj = JobDescription.objects.create(description_text=job_description, user = request.user)
                
                with open(customized_resume_path, 'rb') as f:
                    customized_resume_file = ContentFile(f.read())
                    filename = f'customized_resume_{master_resume.id}.pdf'
                    customized_resume = CustomizedResume.objects.create(
                        master_resume=master_resume,
                        job_description=job_description_obj,
                        user = request.user
                    )
                    customized_resume.customized_resume_file.save(filename, customized_resume_file)
                
                logger.info(f"Successfully saved customized resume with ID: {customized_resume.id}")
            except Exception as e:
                logger.error(f"Error saving to database: {str(e)}")
                raise ValidationError(f"Error saving customized resume: {str(e)}")

            return Response({
                'customized_resume_file': customized_resume.customized_resume_file.url,
                'message': 'Resume customized successfully'
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except APIException as e:
            return Response({'error': str(e)}, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.error(f"Error cleaning up file {temp_file}: {str(e)}")

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

            Please provide the customized resume content maintaining a professional format Don't return any extra text.
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
            # Create a unique filename
            filename = f'customized_resume_{uuid.uuid4()}.pdf'
            output_path = os.path.join(settings.MEDIA_ROOT, 'customized_resumes', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create the PDF
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Set font and size
            c.setFont("Helvetica", 12)
            
            # Split text into lines that fit the page width
            y = height - 50  # Start 50 points from top
            margin = 50
            line_height = 14
            available_width = width - 2 * margin
            
            # Split text into paragraphs
            paragraphs = text.split('\n')
            
            for paragraph in paragraphs:
                # Wrap text to fit page width
                lines = textwrap.wrap(paragraph, width=80)  # Approximate characters per line
                
                for line in lines:
                    if y < 50:  # If we're near the bottom, start a new page
                        c.showPage()
                        y = height - 50
                        c.setFont("Helvetica", 12)
                    
                    c.drawString(margin, y, line)
                    y -= line_height
                
                # Add space between paragraphs
                y -= line_height
            
            c.save()
            logger.info(f"Successfully created PDF at: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating PDF: {str(e)}", exc_info=True)
            raise Exception(f"Error creating PDF: {str(e)}")