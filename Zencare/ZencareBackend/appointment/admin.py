from django.contrib import admin
from .models import Appointment, MedicalReport, Prescription

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient__email', 'doctor__email', 'symptoms')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-appointment_date', '-appointment_time')

@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'lab_technician', 'report_type', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('patient__email', 'doctor__email', 'lab_technician__email', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'doctor_name', 'appointment_date', 'appointment_time', 'status', 'created_at')
    list_filter = ('lab_tests_required', 'status', 'created_at')
    search_fields = ('patient_name', 'doctor_name', 'symptoms', 'prescription_text')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Patient & Doctor', {
            'fields': ('patient', 'patient_name', 'doctor', 'doctor_name', 'doctor_profession')
        }),
        ('Appointment Details', {
            'fields': ('appointment', 'appointment_date', 'appointment_time', 'symptoms')
        }),
        ('Prescription', {
            'fields': ('prescription_text',)
        }),
        ('Lab Information', {
            'fields': ('lab_tests_required', 'lab_instructions', 'lab_technician', 'lab_results', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
