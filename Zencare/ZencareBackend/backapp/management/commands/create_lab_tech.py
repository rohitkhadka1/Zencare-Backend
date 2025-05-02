from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a lab technician user'

    def handle(self, *args, **options):
        # Check if the user already exists
        if User.objects.filter(email='labtechnician@zencare.com').exists():
            self.stdout.write(self.style.WARNING('Lab technician user already exists'))
            return
        
        # Create the lab technician user
        user = User.objects.create_user(
            email='labtechnician@zencare.com',
            password='labtechnician@zencare',
            user_type='lab_technician',
            first_name='Lab',
            last_name='Technician',
            is_profile_completed=True,
            is_verified=True,
            city='Your City',
            state='Your State',
            country='Your Country',
            phone_number='1234567890',
            date_of_birth='1990-01-01',
            address='123 Lab Street',
            gender='O'  # Other gender
        )
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created lab technician user: {user.email}')) 