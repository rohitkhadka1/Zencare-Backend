from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Appointment
from .serializers import AppointmentSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

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

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'doctor':
            return Appointment.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Appointment.objects.filter(patient=user)
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
        raise PermissionDenied("Invalid user type")

    def perform_update(self, serializer):
        user = self.request.user
        appointment = self.get_object()
        
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
        if user.user_type != 'patient' or instance.patient != user:
            raise PermissionDenied("Only the patient who created the appointment can delete it")
        instance.delete()
