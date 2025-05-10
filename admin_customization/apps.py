from django.apps import AppConfig
from django.contrib import admin


class AdminCustomizationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_customization'
    verbose_name = 'Admin Customization'

    def ready(self):
        """
        Initialize the admin customization.
        """
        try:
            # Import the custom admin site
            from .admin import zencare_admin
            
            # Replace the default admin site
            admin.site = zencare_admin
        except Exception as e:
            print(f"Error in admin_customization.apps.ready(): {e}")
