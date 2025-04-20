from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Patient details for this appointment - making some optional
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, help_text="Height in cm", blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg", blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Medical information
    symptoms = models.TextField(help_text="Current symptoms or reason for appointment", blank=True)
    medical_history = models.TextField(blank=True, help_text="Any previous medical conditions or allergies")
    current_medications = models.TextField(blank=True, help_text="Current medications being taken")
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_policy_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.get_full_name()} on {self.appointment_date} at {self.appointment_time}"

class MedicalReport(models.Model):
    REPORT_TYPE_CHOICES = (
        ('blood_test', 'Blood Test'),
        ('urine_test', 'Urine Test'),
        ('x_ray', 'X-Ray'),
        ('mri', 'MRI Scan'),
        ('ct_scan', 'CT Scan'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG'),
        ('other', 'Other'),
    )

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='medical_reports')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_reports')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_reports')
    lab_technician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='technician_reports')
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    report_file = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])]
    )
    description = models.TextField(help_text="Description of the report")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_type_display()} for {self.patient.get_full_name()} - {self.created_at.strftime('%Y-%m-%d')}"

class Prescription(models.Model):
    """
    Prescription model to store doctor's instructions for patients and lab technicians.
    This connects the doctor, patient, and appointment.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending Lab Tests'),
        ('completed', 'Completed'),
    )
    
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_prescriptions')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_prescriptions')
    
    # Doctor's prescription details
    diagnosis = models.TextField(help_text="Doctor's diagnosis")
    medication = models.TextField(help_text="Prescribed medications")
    instructions = models.TextField(help_text="Instructions for the patient")
    
    # Lab test related fields
    lab_tests_required = models.BooleanField(default=False, help_text="Whether lab tests are required")
    lab_instructions = models.TextField(blank=True, help_text="Instructions for the lab technician")
    lab_technician = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='lab_prescriptions',
        null=True, 
        blank=True,
        help_text="Assigned lab technician"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prescription for {self.patient.get_full_name()} by Dr. {self.doctor.get_full_name()}"
