from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Appointment
from django.utils import timezone

User = get_user_model()

class AppointmentSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('patient', 'created_at', 'updated_at')

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.get_full_name()}"

    def get_patient_name(self, obj):
        return obj.patient.get_full_name()

    def validate(self, data):
        # Check if the selected doctor is actually a doctor
        if data['doctor'].user_type != 'doctor':
            raise serializers.ValidationError({"doctor": "Selected user is not a doctor"})
        
        # Check if the appointment time is in the future
        appointment_datetime = timezone.datetime.combine(
            data['appointment_date'], 
            data['appointment_time'],
            tzinfo=timezone.get_current_timezone()
        )
        if appointment_datetime <= timezone.now():
            raise serializers.ValidationError({"appointment_time": "Appointment time must be in the future"})
        
        return data 