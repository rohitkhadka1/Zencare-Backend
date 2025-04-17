from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates dummy doctors for testing'

    def handle(self, *args, **kwargs):
        # List of dummy doctors
        doctors = [
            {
                'email': 'john.smith@zencare.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'password': 'Doctor123!',
                'profession': 'general',
                'phone_number': '123-456-7890',
                'address': '123 Medical Center Dr, New York, NY'
            },
            {
                'email': 'sarah.jones@zencare.com',
                'first_name': 'Sarah',
                'last_name': 'Jones',
                'password': 'Doctor123!',
                'profession': 'dentist',
                'phone_number': '234-567-8901',
                'address': '456 Dental Suite, Boston, MA'
            },
            {
                'email': 'michael.patel@zencare.com',
                'first_name': 'Michael',
                'last_name': 'Patel',
                'password': 'Doctor123!',
                'profession': 'dermatologist',
                'phone_number': '345-678-9012',
                'address': '789 Skin Care Ave, Los Angeles, CA'
            },
            {
                'email': 'emily.chen@zencare.com',
                'first_name': 'Emily',
                'last_name': 'Chen',
                'password': 'Doctor123!',
                'profession': 'ophthalmologist',
                'phone_number': '456-789-0123',
                'address': '321 Vision Center, Chicago, IL'
            },
            {
                'email': 'david.wilson@zencare.com',
                'first_name': 'David',
                'last_name': 'Wilson',
                'password': 'Doctor123!',
                'profession': 'pediatrician',
                'phone_number': '567-890-1234',
                'address': '654 Children\'s Clinic, Seattle, WA'
            },
            {
                'email': 'lisa.brown@zencare.com',
                'first_name': 'Lisa',
                'last_name': 'Brown',
                'password': 'Doctor123!',
                'profession': 'psychiatrist',
                'phone_number': '678-901-2345',
                'address': '987 Mental Health Blvd, Miami, FL'
            }
        ]

        for doctor_data in doctors:
            try:
                user = User.objects.create_user(
                    email=doctor_data['email'],
                    password=doctor_data['password'],
                    first_name=doctor_data['first_name'],
                    last_name=doctor_data['last_name'],
                    user_type='doctor',
                    profession=doctor_data['profession'],
                    phone_number=doctor_data['phone_number'],
                    address=doctor_data['address'],
                    is_active=True,
                    is_verified=True,
                    date_of_birth=timezone.now().date()
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created doctor: {user.email}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to create doctor {doctor_data["email"]}: {str(e)}')) 