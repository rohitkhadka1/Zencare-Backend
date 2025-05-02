from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Create admin, doctor, and lab technician users'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email for the user')
        parser.add_argument('--password', type=str, help='Password for the user')
        parser.add_argument('--first_name', type=str, help='First name of the user')
        parser.add_argument('--last_name', type=str, help='Last name of the user')
        parser.add_argument('--user_type', type=str, choices=['admin', 'doctor', 'lab_technician'], help='Type of user to create')
        parser.add_argument('--profession', type=str, help='Profession for doctor (required for doctors)')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        user_type = options['user_type']
        profession = options.get('profession')

        if not all([email, password, first_name, last_name, user_type]):
            self.stdout.write(self.style.ERROR('All fields are required except profession (only required for doctors)'))
            return

        if user_type == 'doctor' and not profession:
            self.stdout.write(self.style.ERROR('Profession is required for doctors'))
            return

        try:
            with transaction.atomic():
                if user_type == 'admin':
                    user = User.objects.create_superuser(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        user_type='admin'
                    )
                else:
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        user_type=user_type,
                        profession=profession if user_type == 'doctor' else None,
                        is_profile_completed=True
                    )

                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {user_type} user: {email}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create user: {str(e)}')
            ) 