from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.contrib.auth import get_user_model
from .serializers import CreateStaffUserSerializer, UserProfileSerializer
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.exceptions import ValidationError

User = get_user_model()

class IsAdminOrSuperuser(BasePermission):
    """
    Custom permission to only allow admins or superusers to access the view
    """
    def has_permission(self, request, view):
        return bool(request.user and (request.user.user_type == 'admin' or request.user.is_superuser))


class AdminUserViewSet(viewsets.ModelViewSet):
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    permission_classes = [IsAuthenticated, IsAdminOrSuperuser]
    
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