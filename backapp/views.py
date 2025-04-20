from django.shortcuts import render
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, DoctorListSerializer, 
    UserProfileSerializer, CompleteProfileSerializer, CreateStaffUserSerializer,
    ProfileDetailsSerializer
)
import logging
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework_simplejwt.views import TokenRefreshView
from django.core.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action

logger = logging.getLogger(__name__)

User = get_user_model()

class IsAdminOrSuperuser(IsAdminUser):
    def has_permission(self, request, view):
        return bool(request.user and (request.user.user_type == 'admin' or request.user.is_superuser))

# Create your views here.

class HomeView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Welcome to Zencare API',
            'endpoints': {
                'register': '/auth/register/',
                'login': '/auth/login/',
                'doctors': '/doctors/',
                'token_refresh': '/auth/token/refresh/',
                'profile': '/profile/',
                'profile-details': '/profile-details/',
                'complete-profile': '/complete-profile/',
                'admin': {
                    'doctors': '/admin/doctors/',
                    'patients': '/admin/patients/',
                    'lab-technicians': '/admin/lab-technicians/',
                },
                'appointments': {
                    'list': '/appointment/',
                    'create': '/appointment/create/',
                    'detail': '/appointment/<id>/',
                    'pending': '/appointment/pending/'  # For doctors to see pending appointments
                },
                'reports': {
                    'list': '/appointment/reports/',
                    'create': '/appointment/reports/create/',
                    'detail': '/appointment/reports/<id>/'
                },
                'prescriptions': {
                    'list': '/appointment/prescriptions/',
                    'create': '/appointment/prescriptions/create/',
                    'detail': '/appointment/prescriptions/<id>/',
                    'lab_tests': '/appointment/lab-tests-required/'  # For lab technicians
                }
            }
        })

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                logger.info(f"User registered successfully: {user.email}")
                return Response({
                    'user': serializer.data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'is_profile_completed': user.is_profile_completed
                }, status=status.HTTP_201_CREATED)
            logger.error(f"Registration validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.error(f"Registration validation error: {str(e)}")
            return Response({
                'error': 'Validation error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'error': 'An error occurred during registration',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                refresh = RefreshToken.for_user(user)
                logger.info(f"User logged in successfully: {user.email}")
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user_id': user.id,
                    'email': user.email,
                    'user_type': user.user_type,
                    'is_profile_completed': user.is_profile_completed
                })
            logger.error(f"Login validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                'error': 'An error occurred during login',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileCompletionView(generics.UpdateAPIView):
    serializer_class = CompleteProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
        
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Only allow patients to complete their profile
        if user.user_type != 'patient':
            return Response(
                {"detail": "Only patients need to complete their profile"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if profile is already completed
        if user.is_profile_completed:
            return Response(
                {"detail": "Your profile is already completed"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        return super().update(request, *args, **kwargs)

class DoctorListView(generics.ListAPIView):
    serializer_class = DoctorListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'profession', 'address']
    ordering_fields = ['first_name', 'last_name', 'profession']

    def get_queryset(self):
        queryset = User.objects.filter(user_type='doctor', is_active=True)
        
        # Filter by profession if provided
        profession = self.request.query_params.get('profession', None)
        if profession:
            queryset = queryset.filter(profession=profession)
            
        return queryset

class AdminUserViewSet(viewsets.ModelViewSet):
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    
    def get_permissions(self):
        # Only admins can access these endpoints
        return [IsAuthenticated(), IsAdminOrSuperuser()]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CreateStaffUserSerializer
        return UserProfileSerializer
    
    def perform_destroy(self, instance):
        # Make sure admins can't delete themselves or other admins
        if instance.user_type == 'admin':
            raise ValidationError("Cannot delete admin users")
        instance.delete()

class DoctorAdminViewSet(AdminUserViewSet):
    def get_queryset(self):
        return User.objects.filter(user_type='doctor')
        
    def perform_create(self, serializer):
        # Force user_type to doctor
        serializer.save(user_type='doctor')

class LabTechnicianAdminViewSet(AdminUserViewSet):
    def get_queryset(self):
        return User.objects.filter(user_type='lab_technician')
        
    def perform_create(self, serializer):
        # Force user_type to lab_technician
        serializer.save(user_type='lab_technician')

class PatientAdminViewSet(AdminUserViewSet):
    def get_queryset(self):
        return User.objects.filter(user_type='patient')

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

class ProfileDetailsView(generics.RetrieveAPIView):
    """
    View for retrieving just the profile details that users enter during first login.
    This view focuses specifically on the personal information fields.
    """
    serializer_class = ProfileDetailsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Add a message for patients who haven't completed their profile
        if instance.user_type == 'patient' and not instance.is_profile_completed:
            return Response({
                'profile': serializer.data,
                'message': 'Your profile is incomplete. Please complete your profile information.'
            })
        
        return Response(serializer.data)