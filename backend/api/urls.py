from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MasterResumeViewSet, JobDescriptionViewSet, CustomizedResumeViewSet

router = DefaultRouter()
router.register(r'master-resumes', MasterResumeViewSet)
router.register(r'job-descriptions', JobDescriptionViewSet)
router.register(r'customized-resumes', CustomizedResumeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]