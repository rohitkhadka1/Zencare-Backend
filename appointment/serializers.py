from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Appointment, MedicalReport, Prescription
from django.utils import timezone
from datetime import datetime, time

User = get_user_model()

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    doctor_profession = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            'id', 'doctor', 'doctor_name', 'doctor_profession', 
            'patient_name', 'appointment_date', 'appointment_time',
            'status', 'status_display', 'gender', 'blood_group',
            'height', 'weight', 'emergency_contact_name',
            'emergency_contact_phone', 'symptoms', 'medical_history',
            'current_medications', 'insurance_provider',
            'insurance_policy_number', 'created_at', 'updated_at'
        )
        read_only_fields = ('patient', 'created_at', 'updated_at', 'doctor_name', 
                           'patient_name', 'doctor_profession', 'status_display')
        extra_kwargs = {
            # Only appointment date, time and doctor are strictly required
            'gender': {'required': False},
            'blood_group': {'required': False},
            'height': {'required': False},
            'weight': {'required': False},
            'emergency_contact_name': {'required': False},
            'emergency_contact_phone': {'required': False},
            'symptoms': {'required': False},
        }

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()
    
    def get_doctor_profession(self, obj):
        return obj.doctor.get_profession_display()
    
    def get_status_display(self, obj):
        return obj.get_status_display()

    def validate(self, data):
        # Check if the selected doctor is actually a doctor
        if 'doctor' in data:
            try:
                # Get the doctor object by ID if an integer was passed
                if isinstance(data['doctor'], int):
                    doctor = User.objects.get(id=data['doctor'], user_type='doctor')
                    # Replace the ID with the actual doctor object
                    data['doctor'] = doctor
                elif hasattr(data['doctor'], 'user_type') and data['doctor'].user_type != 'doctor':
                    raise serializers.ValidationError({"doctor": "Selected user is not a doctor"})
            except User.DoesNotExist:
                raise serializers.ValidationError({"doctor": "Doctor with this ID does not exist"})
        
        # Check if the appointment time is in the future
        if 'appointment_date' in data and 'appointment_time' in data:
            appointment_datetime = timezone.datetime.combine(
                data['appointment_date'], 
                data['appointment_time'],
                tzinfo=timezone.get_current_timezone()
            )
            if appointment_datetime <= timezone.now():
                raise serializers.ValidationError({"appointment_time": "Appointment time must be in the future"})
            
            # Check if appointment time is during business hours (9 AM to 5 PM)
            appointment_time = data['appointment_time']
            if appointment_time < time(9, 0) or appointment_time > time(17, 0):
                raise serializers.ValidationError(
                    {"appointment_time": "Appointments must be scheduled between 9 AM and 5 PM"}
                )
        
        # Check if the doctor already has an appointment at this time
        if 'doctor' in data and 'appointment_date' in data and 'appointment_time' in data:
            doctor_id = data['doctor'].id if hasattr(data['doctor'], 'id') else data['doctor']
            existing_appointment = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=data['appointment_date'],
                appointment_time=data['appointment_time']
            ).exists()
            
            if existing_appointment:
                raise serializers.ValidationError(
                    {"appointment_time": "This time slot is already booked for the selected doctor"}
                )
        
        return data

class MedicalReportSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    lab_technician_name = serializers.SerializerMethodField()
    report_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicalReport
        fields = (
            'id', 'appointment', 'patient', 'doctor', 'lab_technician',
            'doctor_name', 'patient_name', 'lab_technician_name',
            'report_type', 'report_type_display', 'report_file',
            'description', 'notes', 'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at', 'doctor_name', 
                           'patient_name', 'lab_technician_name', 
                           'report_type_display')
    
    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"
    
    def get_patient_name(self, obj):
        return obj.patient.get_full_name()
    
    def get_lab_technician_name(self, obj):
        return obj.lab_technician.get_full_name()
    
    def get_report_type_display(self, obj):
        return obj.get_report_type_display()
    
    def validate(self, data):
        # Ensure the lab technician is actually a lab technician
        if self.context['request'].user.user_type != 'lab_technician':
            raise serializers.ValidationError("Only lab technicians can upload medical reports")
        
        # Ensure appointment exists and is completed
        if data['appointment'].status != 'completed':
            raise serializers.ValidationError({
                "appointment": "Reports can only be uploaded for completed appointments"
            })
        
        # Ensure patient and doctor match the appointment
        if data['patient'] != data['appointment'].patient:
            raise serializers.ValidationError({
                "patient": "Patient does not match the appointment"
            })
        
        if data['doctor'] != data['appointment'].doctor:
            raise serializers.ValidationError({
                "doctor": "Doctor does not match the appointment"
            })
        
        return data 

class PrescriptionSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()
    lab_technician_name = serializers.SerializerMethodField()
    appointment_details = serializers.SerializerMethodField()
    medical_reports = serializers.SerializerMethodField()

    # Explicitly declare all fields with required=False to override model constraints
    doctor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    patient = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    appointment = serializers.PrimaryKeyRelatedField(queryset=Appointment.objects.all(), required=False, allow_null=True)
    lab_technician = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    
    # Fields that are part of the model but need to be explicitly declared as non-required
    symptoms = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    appointment_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    appointment_date = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    prescription_text = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    lab_tests_required = serializers.BooleanField(required=False, allow_null=True)
    lab_instructions = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    status = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # Adding old field names as explicit serializer fields
    diagnosis = serializers.CharField(required=False, write_only=True, allow_null=True, allow_blank=True)
    medication = serializers.CharField(required=False, write_only=True, allow_null=True, allow_blank=True)
    instructions = serializers.CharField(required=False, write_only=True, allow_null=True, allow_blank=True)
    
    # Also accept ID fields directly
    doctor_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    patient_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    appointment_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    lab_technician_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)
    
    class Meta:
        model = Prescription
        fields = (
            'id', 'appointment', 'patient', 'doctor', 'doctor_name', 'patient_name',
            'symptoms', 'appointment_time', 'appointment_date', 'prescription_text',
            'lab_tests_required', 'lab_instructions', 'lab_technician', 'lab_technician_name',
            'status', 'appointment_details', 'medical_reports', 'created_at', 'updated_at',
            # Include the old field names
            'diagnosis', 'medication', 'instructions',
            # Include ID fields 
            'doctor_id', 'patient_id', 'appointment_id', 'lab_technician_id'
        )
        read_only_fields = ('created_at', 'updated_at', 'doctor_name', 'patient_name', 
                           'lab_technician_name', 'appointment_details', 'medical_reports')
    
    def get_doctor_name(self, obj):
        if obj.doctor:
            return f"Dr. {obj.doctor.get_full_name()}"
        return None
    
    def get_patient_name(self, obj):
        if obj.patient:
            return obj.patient.get_full_name()
        return None
    
    def get_lab_technician_name(self, obj):
        if obj.lab_technician:
            return obj.lab_technician.get_full_name()
        return None
    
    def get_appointment_details(self, obj):
        if obj.appointment:
            return {
                'date': obj.appointment.appointment_date,
                'time': obj.appointment.appointment_time,
                'status': obj.appointment.status
            }
        return None
    
    def get_medical_reports(self, obj):
        # Get related medical reports if any
        if obj.appointment:
            reports = MedicalReport.objects.filter(appointment=obj.appointment)
            if reports.exists():
                return MedicalReportSerializer(reports, many=True).data
        return []
    
    def validate(self, data):
        # Map old field names to new field names if provided
        if 'diagnosis' in data:
            data['symptoms'] = data.pop('diagnosis')
            
        if 'medication' in data:
            data['appointment_time'] = data.pop('medication')
            
        if 'instructions' in data:
            data['appointment_date'] = data.pop('instructions')
            
        # Handle ID fields
        if 'doctor_id' in data and not 'doctor' in data:
            try:
                data['doctor'] = User.objects.get(id=data.pop('doctor_id'))
            except Exception:
                pass
                
        if 'patient_id' in data and not 'patient' in data:
            try:
                data['patient'] = User.objects.get(id=data.pop('patient_id'))
            except Exception:
                pass
                
        if 'appointment_id' in data and not 'appointment' in data:
            try:
                data['appointment'] = Appointment.objects.get(id=data.pop('appointment_id'))
            except Exception:
                pass
                
        if 'lab_technician_id' in data and not 'lab_technician' in data:
            try:
                data['lab_technician'] = User.objects.get(id=data.pop('lab_technician_id'))
            except Exception:
                pass
        
        # All validations are now optional
        return data

class PrescriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating prescriptions with lab results
    """
    class Meta:
        model = Prescription
        fields = ('lab_technician', 'status')
    
    def validate(self, data):
        # All validations are now optional
        return data 