from django.apps import AppConfig
from django.contrib import admin


class AdminCustomizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_customization'
    
    def ready(self):
        """
        Initialize custom admin site on app ready.
        """
        try:
            # Import here to avoid circular imports
            from backapp.models import User
            from appointment.models import Appointment, MedicalReport, Prescription
            from appointment.admin import AppointmentAdmin, MedicalReportAdmin, PrescriptionAdmin
            from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
            from .admin import zencare_admin
            
            # Create a custom UserAdmin that works with your User model
            class CustomUserAdmin(BaseUserAdmin):
                # Use email as the unique identifier instead of username
                ordering = ('email',)
                list_display = ('email', 'first_name', 'last_name', 'is_staff', 'user_type', 'is_profile_completed')
                search_fields = ('email', 'first_name', 'last_name', 'phone_number')
                list_filter = ('user_type', 'is_staff', 'is_active', 'is_profile_completed')
                
                # Different fieldsets for different user types
                fieldsets = (
                    (None, {'fields': ('email', 'password')}),
                    ('Personal info', {'fields': ('first_name', 'last_name', 'user_type', 'date_of_birth', 'gender')}),
                    ('Contact Details', {'fields': ('phone_number', 'phone_number_2', 'address', 'city', 'state', 'country')}),
                    ('Status', {'fields': ('is_verified', 'is_profile_completed')}),
                    ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
                    ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
                )
                
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
            
            # Register models with our custom admin site
            zencare_admin.register(User, CustomUserAdmin)
            zencare_admin.register(Appointment, AppointmentAdmin)
            zencare_admin.register(MedicalReport, MedicalReportAdmin)
            zencare_admin.register(Prescription, PrescriptionAdmin)
            
            # Replace the default admin site
            admin.site = zencare_admin
        except Exception as e:
            print(f"Error in admin_customization.apps.ready(): {e}")
