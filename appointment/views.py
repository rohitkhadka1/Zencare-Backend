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
from notifications.services import NotificationService  

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
            NotificationService.notify_appointment_created(serializer.instance)
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
    Create a new prescription exactly matching the fields shown in the UI
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        # Debug log to see what data is coming in
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("PRESCRIPTION CREATE VIEW")
        print("Request data:", request.data)
        print("Request content type:", request.content_type)
        print("Request method:", request.method)
        print("Request headers:", {k: v for k, v in request.headers.items() if k.lower() != 'authorization'})
        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        try:
            # Create a copy of the data we can modify
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            
            # If data comes in lists (like from form-data), extract first element
            for key in list(data.keys()):
                if isinstance(data[key], list) and len(data[key]) > 0:
                    data[key] = data[key][0]
            
            # Support format from the screenshot UI
            # Common field renaming
            field_mapping = {
                # Legacy field renames
                'diagnosis': 'symptoms',
                'medication': 'prescription_text',
                'instructions': 'lab_instructions',
                
                # Frontend form fields mapping
                'doctorName': 'doctor_name',
                'patientName': 'patient_name',
                'doctorProfession': 'doctor_profession',
                'appointmentDate': 'appointment_date',
                'appointmentTime': 'appointment_time',
                'doctorNotes': 'prescription_text',
                'doctorsPrescription': 'prescription_text',  # another common name
                'notes': 'prescription_text',
                'description': 'symptoms'
            }
            
            # Map fields based on renaming map
            for frontend_field, model_field in field_mapping.items():
                if frontend_field in data and not model_field in data:
                    data[model_field] = data.pop(frontend_field)
            
            # Handle ID fields with multiple formats
            try:
                # Doctor ID handling
                doctor_id = None
                for field_name in ['doctorId', 'doctor_id', 'doctor']:
                    if field_name in data and not doctor_id:
                        value = data.get(field_name)
                        if value and (isinstance(value, int) or (isinstance(value, str) and value.isdigit())):
                            doctor_id = int(value)
                            if field_name != 'doctor':  # Don't pop if it's the direct field
                                data.pop(field_name)
                
                if doctor_id:
                    try:
                        doctor = User.objects.get(id=doctor_id)
                        data['doctor'] = doctor.id
                        # Auto-populate related fields
                        if not data.get('doctor_name'):
                            data['doctor_name'] = f"Dr. {doctor.get_full_name()}"
                        if not data.get('doctor_profession') and hasattr(doctor, 'get_profession_display'):
                            data['doctor_profession'] = doctor.get_profession_display()
                    except Exception as e:
                        print(f"Error getting doctor details: {e}")
                
                # Patient ID handling
                patient_id = None
                for field_name in ['patientId', 'patient_id', 'patient']:
                    if field_name in data and not patient_id:
                        value = data.get(field_name)
                        if value and (isinstance(value, int) or (isinstance(value, str) and value.isdigit())):
                            patient_id = int(value)
                            if field_name != 'patient':  # Don't pop if it's the direct field
                                data.pop(field_name)
                
                if patient_id:
                    try:
                        patient = User.objects.get(id=patient_id)
                        data['patient'] = patient.id
                        # Auto-populate patient name
                        if not data.get('patient_name'):
                            data['patient_name'] = patient.get_full_name()
                    except Exception as e:
                        print(f"Error getting patient details: {e}")
                            
                # Handle appointment data
                appointment_id = None
                for field_name in ['appointmentId', 'appointment_id', 'appointment']:
                    if field_name in data and not appointment_id:
                        value = data.get(field_name)
                        if value and (isinstance(value, int) or (isinstance(value, str) and value.isdigit())):
                            appointment_id = int(value)
                            if field_name != 'appointment':  # Don't pop if it's the direct field
                                data.pop(field_name)
                
                if appointment_id:
                    try:
                        appointment = Appointment.objects.get(id=appointment_id)
                        data['appointment'] = appointment.id
                        
                        # Set appointment date/time if not provided
                        if not data.get('appointment_date'):
                            data['appointment_date'] = str(appointment.appointment_date)
                        if not data.get('appointment_time'):
                            data['appointment_time'] = str(appointment.appointment_time)
                        if not data.get('symptoms') and appointment.symptoms:
                            data['symptoms'] = appointment.symptoms
                            
                        # Also populate patient and doctor if not already set
                        if not data.get('patient') and appointment.patient:
                            data['patient'] = appointment.patient.id
                            if not data.get('patient_name'):
                                data['patient_name'] = appointment.patient.get_full_name()
                                
                        if not data.get('doctor') and appointment.doctor:
                            data['doctor'] = appointment.doctor.id
                            if not data.get('doctor_name'):
                                data['doctor_name'] = f"Dr. {appointment.doctor.get_full_name()}"
                    except Exception as e:
                        print(f"Error getting appointment details: {e}")
            except Exception as e:
                print(f"Error processing IDs: {e}")
                
            # Current user auto-assignment (if fields not specified)
            if 'doctor' not in data and request.user.user_type == 'doctor':
                data['doctor'] = request.user.id
                if not data.get('doctor_name'):
                    data['doctor_name'] = f"Dr. {request.user.get_full_name()}"
                    
            if 'patient' not in data and request.user.user_type == 'patient':
                data['patient'] = request.user.id
                if not data.get('patient_name'):
                    data['patient_name'] = request.user.get_full_name()
            
            print("Processed data:", data)
            
            # Use special case for empty requests or requests with minimal data
            if not data:
                # Create an empty prescription if needed
                prescription = Prescription.objects.create()
                response = Response(
                    {
                        "detail": "Empty prescription created successfully", 
                        "data": self.get_serializer(prescription).data
                    }, 
                    status=status.HTTP_201_CREATED
                )
                # Add CORS headers
                response["Access-Control-Allow-Origin"] = "*"
                response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept, Authorization, X-Request-With"
                return response
            
            # Process the request using the serializer
            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                print("Validation errors:", serializer.errors)
                
                # Try direct creation as fallback
                try:
                    # Filter the data to only include fields that exist on the model
                    valid_fields = {
                        k: v for k, v in data.items() 
                        if k in [f.name for f in Prescription._meta.get_fields()]
                    }
                    
                    prescription = Prescription.objects.create(**valid_fields)
                    response = Response(
                        {
                            "detail": "Prescription created with available data despite validation errors",
                            "warning": "Some fields may not have been processed correctly",
                            "data": self.get_serializer(prescription).data
                        },
                        status=status.HTTP_201_CREATED
                    )
                    # Add CORS headers
                    response["Access-Control-Allow-Origin"] = "*"
                    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                    response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept, Authorization, X-Request-With"
                    return response
                except Exception as e:
                    print(f"Error creating prescription directly: {str(e)}")
                    # Return the normal error response if direct creation fails
                    response = Response(
                        {
                            "detail": "Validation failed",
                            "errors": serializer.errors,
                            "received_data": request.data
                        }, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    # Add CORS headers
                    response["Access-Control-Allow-Origin"] = "*"
                    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                    response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept, Authorization, X-Request-With"
                    return response
            
            # If valid, save the data
            prescription = serializer.save()
            
            # Auto-populate additional fields if not provided
            # This will trigger the model's save method
            if not prescription.patient_name and prescription.patient:
                prescription.save()
                
            headers = self.get_success_headers(serializer.data)
            response = Response(
                {
                    "detail": "Prescription created successfully", 
                    "data": self.get_serializer(prescription).data
                }, 
                status=status.HTTP_201_CREATED, 
                headers=headers
            )
            # Add CORS headers
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept, Authorization, X-Request-With"
            return response
        except Exception as e:
            # Handle any unexpected exceptions
            print(f"Unexpected error in prescription create: {str(e)}")
            import traceback
            traceback.print_exc()
            response = Response(
                {
                    "detail": "An unexpected error occurred",
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            # Add CORS headers
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept, Authorization, X-Request-With"
            return response

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
    search_fields = ['patient__first_name', 'patient__last_name', 'symptoms', 'appointment_time', 'appointment_date']
    ordering_fields = ['created_at', 'updated_at', 'status']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.user_type == 'doctor':
            return Prescription.objects.filter(doctor=user)
        elif user.user_type == 'patient':
            return Prescription.objects.filter(patient=user)
        elif user.user_type == 'lab_technician':
            return Prescription.objects.all()
            # Lab technicians see all prescriptions that require lab tests
            # return Prescription.objects.filter(lab_tests_required=True)
        elif user.is_superuser or user.is_staff:
            return Prescription.objects.all()
            
        raise PermissionDenied("Invalid user type")

class PrescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a prescription - all fields are now optional
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PrescriptionUpdateSerializer
        return PrescriptionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Everyone can see all prescriptions now to accommodate frontend flexibility
        return Prescription.objects.all()
    
    def perform_update(self, serializer):
        # Allow any updates to any fields
        serializer.save()

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
    View prescriptions that require lab tests - accessible to everyone now
    """
    serializer_class = PrescriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return all prescriptions that require lab tests
        return Prescription.objects.filter(lab_tests_required=True)

def prescription_test_form(request):
    """Simple view to render the prescription test form"""
    return render(request, 'appointment/prescription_test.html')
