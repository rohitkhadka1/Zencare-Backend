from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Appointment, MedicalReport
from .serializers import AppointmentSerializer, MedicalReportSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import SearchFilter, OrderingFilter

User = get_user_model()

# Create your views here.

class AppointmentCreateView(generics.CreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure only patients can create appointments
        if self.request.user.user_type != 'patient':
            raise PermissionDenied("Only patients can create appointments")
        
        # Validate doctor exists and is active
        doctor_id = self.request.data.get('doctor')
        try:
            doctor = User.objects.get(id=doctor_id, user_type='doctor', is_active=True)
        except User.DoesNotExist:
            raise PermissionDenied("Invalid or inactive doctor selected")
        
        serializer.save(patient=self.request.user, doctor=doctor)

class AppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['doctor__first_name', 'doctor__last_name', 'symptoms', 'status']
    ordering_fields = ['appointment_date', 'appointment_time', 'status', 'created_at']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'doctor':
            return Appointment.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Appointment.objects.filter(patient=user)
        elif user.is_superuser or user.is_staff:
            # Admin can see all appointments
            return Appointment.objects.all()
        raise PermissionDenied("Invalid user type")

class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'doctor':
            return Appointment.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Appointment.objects.filter(patient=user)
        elif user.is_superuser or user.is_staff:
            # Admin can see all appointments
            return Appointment.objects.all()
        raise PermissionDenied("Invalid user type")

    def perform_update(self, serializer):
        user = self.request.user
        appointment = self.get_object()
        
        # Admins can update any field
        if user.is_superuser or user.is_staff:
            serializer.save()
            return
            
        # Only allow status updates by doctors
        if user.user_type == 'doctor':
            if 'status' in serializer.validated_data:
                serializer.save()
            else:
                raise PermissionDenied("Doctors can only update appointment status")
        # Patients can only cancel appointments
        elif user.user_type == 'patient':
            if 'status' in serializer.validated_data and serializer.validated_data['status'] == 'cancelled':
                serializer.save()
            else:
                raise PermissionDenied("Patients can only cancel appointments")

    def perform_destroy(self, instance):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            instance.delete()
            return
            
        if user.user_type != 'patient' or instance.patient != user:
            raise PermissionDenied("Only the patient who created the appointment can delete it")
        instance.delete()

class MedicalReportCreateView(generics.CreateAPIView):
    serializer_class = MedicalReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def perform_create(self, serializer):
        # Ensure only lab technicians can create reports
        if self.request.user.user_type != 'lab_technician':
            raise PermissionDenied("Only lab technicians can upload medical reports")
        
        serializer.save(lab_technician=self.request.user)

class MedicalReportListView(generics.ListAPIView):
    serializer_class = MedicalReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['report_type', 'description', 'patient__first_name', 'patient__last_name']
    ordering_fields = ['created_at', 'report_type']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'lab_technician':
            return MedicalReport.objects.filter(lab_technician=user)
        elif user.user_type == 'doctor':
            return MedicalReport.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return MedicalReport.objects.filter(patient=user)
        elif user.is_superuser or user.is_staff:
            return MedicalReport.objects.all()
            
        raise PermissionDenied("Invalid user type")

class MedicalReportDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MedicalReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'lab_technician':
            return MedicalReport.objects.filter(lab_technician=user)
        elif user.user_type == 'doctor':
            return MedicalReport.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return MedicalReport.objects.filter(patient=user)
        elif user.is_superuser or user.is_staff:
            return MedicalReport.objects.all()
            
        raise PermissionDenied("Invalid user type")
    
    def perform_update(self, serializer):
        user = self.request.user
        
        # Only lab technicians who created the report or admins can update them
        if user.user_type == 'lab_technician' and self.get_object().lab_technician == user:
            serializer.save()
        elif user.is_superuser or user.is_staff:
            serializer.save()
        else:
            raise PermissionDenied("You don't have permission to update this report")
    
    def perform_destroy(self, instance):
        user = self.request.user
        
        # Only lab technicians who created the report or admins can delete them
        if user.user_type == 'lab_technician' and instance.lab_technician == user:
            instance.delete()
        elif user.is_superuser or user.is_staff:
            instance.delete()
        else:
            raise PermissionDenied("You don't have permission to delete this report")
