from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.models import LogEntry
from django.db.models import Count
from appointment.models import Appointment, MedicalReport, Prescription
from backapp.models import User

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
