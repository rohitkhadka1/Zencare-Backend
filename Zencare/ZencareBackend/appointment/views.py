from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Appointment, MedicalReport, Prescription
from .serializers import (
    AppointmentSerializer, MedicalReportSerializer, 
    PrescriptionSerializer, PrescriptionUpdateSerializer
)
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

    def create(self, request, *args, **kwargs):
        # Debug log to see what data is coming in
        print(f"Received data: {request.data}")
        
        # Map frontend field names to backend field names
        mapped_data = {}
        
        # Check for different frontend formats
        if 'doctorId' in request.data:
            # Format 1: The API adapter format
            mapped_data['doctor'] = request.data.get('doctorId')
            mapped_data['appointment_date'] = request.data.get('date')
            
            # Handle time format without requiring seconds
            time = request.data.get('time')
            if time and ':' in time:
                # Don't add seconds - Django will handle this format
                mapped_data['appointment_time'] = time
            else:
                mapped_data['appointment_time'] = time
                
            # Map symptoms field
            if 'description' in request.data:
                mapped_data['symptoms'] = request.data.get('description')
        
        elif 'doctor' in request.data:
            # Format 2: Direct field names format from api.js
            mapped_data['doctor'] = request.data.get('doctor')
            mapped_data['appointment_date'] = request.data.get('appointment_date')
            
            # Use time as-is without modifying format
            mapped_data['appointment_time'] = request.data.get('appointment_time')
            
            # Map symptoms from description if present
            if 'description' in request.data:
                mapped_data['symptoms'] = request.data.get('description')
        
        else:
            # Use request data as is
            mapped_data = request.data
            
        print(f"Mapped data: {mapped_data}")
        
        # Use the mapped data
        serializer = self.get_serializer(data=mapped_data)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"Validation error: {serializer.errors if hasattr(serializer, 'errors') else str(e)}")
            return Response(
                {"error": serializer.errors if hasattr(serializer, 'errors') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        # Ensure only patients can create appointments
        if self.request.user.user_type != 'patient':
            raise PermissionDenied("Only patients can create appointments")
        
        # Doctor object has already been validated and processed in the serializer's validate method
        # Just save the appointment with the patient as the current user
        serializer.save(patient=self.request.user)

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

class PrescriptionCreateView(generics.CreateAPIView):
    """
    Create a new prescription (doctor only)
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Only doctors can create prescriptions
        if self.request.user.user_type != 'doctor':
            raise PermissionDenied("Only doctors can create prescriptions")
        
        serializer.save(doctor=self.request.user)

class PrescriptionListView(generics.ListAPIView):
    """
    List prescriptions based on user role:
    - Doctors see prescriptions they created
    - Patients see prescriptions prescribed to them
    - Lab technicians see prescriptions with lab_tests_required=True
    - Admins see all prescriptions
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['patient__first_name', 'patient__last_name', 'diagnosis', 'medication']
    ordering_fields = ['created_at', 'updated_at', 'status']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'doctor':
            return Prescription.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Prescription.objects.filter(patient=user)
        elif user.user_type == 'lab_technician':
            # Lab technicians see all prescriptions that require lab tests
            return Prescription.objects.filter(lab_tests_required=True)
        elif user.is_superuser or user.is_staff:
            return Prescription.objects.all()
            
        raise PermissionDenied("Invalid user type")

class PrescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a prescription:
    - Doctors can update diagnosis, medication, instructions
    - Lab technicians can update lab-related fields
    - Patients can only view
    - Admins can do all operations
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        user = self.request.user
        if user.user_type == 'lab_technician':
            return PrescriptionUpdateSerializer
        return PrescriptionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'doctor':
            return Prescription.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Prescription.objects.filter(patient=user)
        elif user.user_type == 'lab_technician':
            # Lab technicians see all prescriptions that require lab tests
            return Prescription.objects.filter(lab_tests_required=True)
        elif user.is_superuser or user.is_staff:
            return Prescription.objects.all()
            
        raise PermissionDenied("Invalid user type")
    
    def perform_update(self, serializer):
        user = self.request.user
        
        if user.is_superuser or user.is_staff:
            serializer.save()
            return
            
        if user.user_type == 'doctor' and self.get_object().doctor == user:
            # Doctors can only update their own prescriptions
            serializer.save()
        elif user.user_type == 'lab_technician':
            # Lab technicians can assign themselves and update status
            serializer.save(lab_technician=user)
        else:
            raise PermissionDenied("You don't have permission to update this prescription")

class PendingAppointmentsView(generics.ListAPIView):
    """
    View for doctors to see their pending appointments
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type != 'doctor':
            raise PermissionDenied("Only doctors can access pending appointments")
            
        # Return pending and confirmed appointments for this doctor
        return Appointment.objects.filter(
            doctor=user, 
            status__in=['pending', 'confirmed']
        ).order_by('appointment_date', 'appointment_time')

class LabTestsRequiredView(generics.ListAPIView):
    """
    View for lab technicians to see prescriptions that require lab tests
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type != 'lab_technician':
            raise PermissionDenied("Only lab technicians can access this view")
            
        # Return prescriptions that require lab tests and don't have a lab technician assigned
        # or are assigned to this lab technician
        return Prescription.objects.filter(
            lab_tests_required=True
        ).filter(
            lab_technician__isnull=True
        ).order_by('created_at')
