from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from appointment.models import Appointment, MedicalReport, Prescription
from backapp.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.

class ZenCareAdminSite(AdminSite):
    site_title = _('ZenCare Admin')
    site_header = _('ZenCare Administration')
    index_title = _('ZenCare Admin Dashboard')

    def index(self, request, extra_context=None):
        """
        Customize the admin index page with additional context data.
        """
        # Get model counts for the dashboard stats
        model_count = {
            'users': User.objects.count(),
            'doctors': User.objects.filter(user_type='doctor').count(),
            'appointments': Appointment.objects.count(),
            'reports': MedicalReport.objects.count(),
            'prescriptions': Prescription.objects.count()
        }

        # Get recent actions for the activity feed
        recent_actions = LogEntry.objects.select_related('content_type', 'user')[:20]

        context = {
            'model_count': model_count,
            'recent_actions': recent_actions,
        }

        if extra_context:
            context.update(extra_context)

        return super().index(request, context)

# Create the custom admin site
zencare_admin = ZenCareAdminSite(name='zencare_admin')

# Custom User Admin
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    # Doctor-specific fieldset that appears only for doctor users
    doctor_fieldsets = (
        ('Doctor Details', {
            'classes': ('collapse',),
            'fields': ('profession', 'experience_years', 'work_experience', 'education', 'training', 'consultation_fee'),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'is_staff', 'is_active'),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        # Add the doctor-specific fieldset only for doctor users
        if obj and obj.user_type == 'doctor':
            return self.fieldsets + self.doctor_fieldsets
        return self.fieldsets

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('patient__email', 'doctor__email')
    ordering = ('-appointment_date',)

class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'created_at')
    search_fields = ('appointment__patient__email', 'appointment__doctor__email')
    ordering = ('-created_at',)

class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'created_at')
    search_fields = ('appointment__patient__email', 'appointment__doctor__email')
    ordering = ('-created_at',)

# Register all models with the custom admin site
zencare_admin.register(User, CustomUserAdmin)
zencare_admin.register(Appointment, AppointmentAdmin)
zencare_admin.register(MedicalReport, MedicalReportAdmin)
zencare_admin.register(Prescription, PrescriptionAdmin)
