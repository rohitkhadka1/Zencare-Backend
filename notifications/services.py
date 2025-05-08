from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Notification

class NotificationService:
    @staticmethod
    def send_email_notification(recipient_email, subject, message, html_message=None):
        """Send an email notification"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    @staticmethod
    def create_notification(recipient, notification_type, title, message, related_object=None):
        """Create a notification record"""
        try:
            notification = Notification.objects.create(
                recipient=recipient,
                notification_type=notification_type,
                title=title,
                message=message,
                related_object_id=related_object.id if related_object else None,
                related_object_type=related_object.__class__.__name__ if related_object else None
            )
            return notification
        except Exception as e:
            print(f"Error creating notification: {str(e)}")
            return None

    @staticmethod
    def notify_appointment_created(appointment):
        """Handle appointment creation notification"""
        # Notify patient
        patient_message = f"Your appointment with Dr. {appointment.doctor.get_full_name()} has been scheduled for {appointment.appointment_date} at {appointment.appointment_time}."
        NotificationService.create_notification(
            recipient=appointment.patient,
            notification_type='appointment_created',
            title='Appointment Scheduled',
            message=patient_message,
            related_object=appointment
        )
        NotificationService.send_email_notification(
            recipient_email=appointment.patient.email,
            subject='Appointment Scheduled',
            message=patient_message
        )

        # Notify doctor
        doctor_message = f"New appointment scheduled with {appointment.patient.get_full_name()} for {appointment.appointment_date} at {appointment.appointment_time}."
        NotificationService.create_notification(
            recipient=appointment.doctor,
            notification_type='appointment_created',
            title='New Appointment',
            message=doctor_message,
            related_object=appointment
        )
        NotificationService.send_email_notification(
            recipient_email=appointment.doctor.email,
            subject='New Appointment',
            message=doctor_message
        )

    @staticmethod
    def notify_appointment_cancelled(appointment):
        """Handle appointment cancellation notification"""
        # Notify patient
        patient_message = f"Your appointment with Dr. {appointment.doctor.get_full_name()} scheduled for {appointment.appointment_date} at {appointment.appointment_time} has been cancelled."
        NotificationService.create_notification(
            recipient=appointment.patient,
            notification_type='appointment_cancelled',
            title='Appointment Cancelled',
            message=patient_message,
            related_object=appointment
        )
        NotificationService.send_email_notification(
            recipient_email=appointment.patient.email,
            subject='Appointment Cancelled',
            message=patient_message
        )

        # Notify doctor
        doctor_message = f"Appointment with {appointment.patient.get_full_name()} scheduled for {appointment.appointment_date} at {appointment.appointment_time} has been cancelled."
        NotificationService.create_notification(
            recipient=appointment.doctor,
            notification_type='appointment_cancelled',
            title='Appointment Cancelled',
            message=doctor_message,
            related_object=appointment
        )
        NotificationService.send_email_notification(
            recipient_email=appointment.doctor.email,
            subject='Appointment Cancelled',
            message=doctor_message
        )

    @staticmethod
    def notify_prescription_uploaded(prescription):
        """Handle prescription upload notification"""
        message = f"Dr. {prescription.doctor.get_full_name()} has uploaded a prescription for your appointment on {prescription.appointment.appointment_date}."
        NotificationService.create_notification(
            recipient=prescription.appointment.patient,
            notification_type='prescription_uploaded',
            title='New Prescription Available',
            message=message,
            related_object=prescription
        )
        NotificationService.send_email_notification(
            recipient_email=prescription.appointment.patient.email,
            subject='New Prescription Available',
            message=message
        )

    @staticmethod
    def notify_report_uploaded(report):
        """Handle lab report upload notification"""
        message = f"A new lab report has been uploaded for your appointment on {report.appointment.appointment_date}."
        NotificationService.create_notification(
            recipient=report.appointment.patient,
            notification_type='report_uploaded',
            title='New Lab Report Available',
            message=message,
            related_object=report
        )
        NotificationService.send_email_notification(
            recipient_email=report.appointment.patient.email,
            subject='New Lab Report Available',
            message=message
        ) 