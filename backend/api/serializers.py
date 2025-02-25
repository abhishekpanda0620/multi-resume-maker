from rest_framework import serializers
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