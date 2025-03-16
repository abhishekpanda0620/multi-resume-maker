from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MasterResumeViewSet, JobDescriptionViewSet, CustomizedResumeViewSet
from .auth_views import LoginView, LogoutView, RegisterView, UserView

router = DefaultRouter()
router.register(r'master-resumes', MasterResumeViewSet)
router.register(r'job-descriptions', JobDescriptionViewSet)
router.register(r'customized-resumes', CustomizedResumeViewSet)

urlpatterns = [
    # Authentication endpoints
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('register', RegisterView.as_view(), name='register'),
    path('user', UserView.as_view(), name='user'),
    path('user/<int:pk>/', UserView.as_view(), name='user-detail'),
    # Direct route to the customize action
    path('customized-resumes/customize', CustomizedResumeViewSet.as_view({'post': 'customize'}), name='customize-resume'),
    
    # API endpoints
    path('', include(router.urls)),
]
