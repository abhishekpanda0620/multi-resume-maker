from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MasterResume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resume_file = models.FileField(upload_to='resumes/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Master Resume"

class JobDescription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=255)
    description_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job Description {self.id}"

    class Meta:
        ordering = ['-created_at']

class CustomizedResume(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    master_resume = models.ForeignKey(MasterResume, on_delete=models.CASCADE)
    job_description = models.ForeignKey(JobDescription, null=True, blank=True, on_delete=models.CASCADE)
    customized_resume_file = models.FileField(upload_to='customized_resumes/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Customized Resume for {self.job_description.job_title} - {self.user.username}"