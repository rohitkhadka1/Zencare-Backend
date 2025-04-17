from django.contrib import admin
from .models import Appointment, MedicalReport

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
