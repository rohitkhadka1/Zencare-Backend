import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZencareBackend.settings')
django.setup()

# Import your User model
from django.contrib.auth import get_user_model
User = get_user_model()

def create_lab_tech():
    # Check if the user already exists
    if User.objects.filter(email='labtechnician@zencare.com').exists():
        print('Lab technician user already exists')
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
    
    print(f'Successfully created lab technician user: {user.email}')

if __name__ == '__main__':
    create_lab_tech() 