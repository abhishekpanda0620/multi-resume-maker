from rest_framework import serializers
from django.contrib.auth.models import User
from .models import MasterResume, JobDescription, CustomizedResume

class MasterResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterResume
        fields = '__all__'

class JobDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescription
        fields = '__all__'

class CustomizedResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomizedResume
        fields = '__all__'
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        # Create and return the user instance
        user = User.objects.create_user(**validated_data)
        return user        