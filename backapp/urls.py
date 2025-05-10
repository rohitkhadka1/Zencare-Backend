from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HomeView,
    UserRegistrationView,
    UserLoginView,
    DoctorListView,
    CustomTokenRefreshView,
    UserProfileView,
    ProfileCompletionView,
    ProfileDetailsView,
    PasswordResetAPIView
)
from .admin_views import (
    DoctorAdminViewSet,
    LabTechnicianAdminViewSet,
    PatientAdminViewSet
)

app_name = 'backapp'

# Set up the router for admin viewsets
router = DefaultRouter()
router.register(r'admin/doctors', DoctorAdminViewSet, basename='admin-doctors')
router.register(r'admin/lab-technicians', LabTechnicianAdminViewSet, basename='admin-lab-technicians')
router.register(r'admin/patients', PatientAdminViewSet, basename='admin-patients')

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/password-reset/', PasswordResetAPIView.as_view(), name='password-reset-api'),
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile-details/', ProfileDetailsView.as_view(), name='profile-details'),
    path('complete-profile/', ProfileCompletionView.as_view(), name='complete-profile'),
    path('', include(router.urls)),
]