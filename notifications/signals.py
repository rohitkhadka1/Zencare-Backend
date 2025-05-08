from django.db.models.signals import post_save
from django.dispatch import receiver
from appointment.models import Appointment, Prescription
from .services import NotificationService

@receiver(post_save, sender=Appointment)
def handle_appointment_notification(sender, instance, created, **kwargs):
    """Handle appointment-related notifications"""
    if created:
        # New appointment created
        NotificationService.notify_appointment_created(instance)
    elif instance.status == 'cancelled':
        # Appointment cancelled
        NotificationService.notify_appointment_cancelled(instance)

@receiver(post_save, sender=Prescription)
def handle_prescription_notification(sender, instance, created, **kwargs):
    """Handle prescription upload notification"""
    if created:
        NotificationService.notify_prescription_uploaded(instance)

# Add this when you create the Report model
# @receiver(post_save, sender=Report)
# def handle_report_notification(sender, instance, created, **kwargs):
#     """Handle lab report upload notification"""
#     if created:
#         NotificationService.notify_report_uploaded(instance) 