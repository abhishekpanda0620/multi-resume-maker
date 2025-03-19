import os
import uuid
import logging
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextBox, LTTextLine, LTChar
import pikepdf

from .models import MasterResume, JobDescription, CustomizedResume
from .serializers import MasterResumeSerializer, JobDescriptionSerializer, CustomizedResumeSerializer, UserSerializer, RegisterSerializer
from .services.resume_customizer import ResumeCustomizer 
from google import genai

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('resume_customizer')

# Authentication Views (unchanged)
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
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        response_data = {
            **serializer.data,
            'accessToken': str(refresh.access_token),
            'refreshToken': str(refresh)
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

class UserView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

# Model ViewSets (unchanged)
class MasterResumeViewSet(viewsets.ModelViewSet):
    queryset = MasterResume.objects.all()
    serializer_class = MasterResumeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MasterResume.objects.filter(user=self.request.user)

class JobDescriptionViewSet(viewsets.ModelViewSet):
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return JobDescription.objects.filter(user=self.request.user)

class CustomizedResumeViewSet(viewsets.ModelViewSet):
    queryset = CustomizedResume.objects.all()
    serializer_class = CustomizedResumeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return CustomizedResume.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def customize(self, request):
        """Customize a resume based on a job description while preserving layout."""
        try:
            # Create service instance
            customizer = ResumeCustomizer(request.user)
            
            # Execute customization
            result = customizer.customize_resume(
                master_resume_file=request.FILES.get('master_resume'),
                job_description=request.data.get('job_description')
            )
            
            return Response({
                'customized_resume_file': result.customized_resume_file.url,
                'message': 'Resume customized successfully'
            }, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)