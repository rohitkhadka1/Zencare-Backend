import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZencareBackend.settings')
django.setup()

# Import models
from appointment.models import Prescription
from django.contrib.auth import get_user_model
User = get_user_model()

# Print available users
print("Available users:")
users = User.objects.all()
for user in users:
    print(f"ID: {user.id}, Email: {user.email}, Type: {user.user_type}")

# Create a prescription
print("\nCreating prescription...")
prescription = Prescription.objects.create(
    symptoms="ufreko, haath bachiyo !!",
    prescription_text="thik parera aau"
)
print(f"Created prescription with ID: {prescription.id}")

# Print all prescriptions
print("\nAll prescriptions:")
prescriptions = Prescription.objects.all()
for p in prescriptions:
    print(f"ID: {p.id}, Symptoms: {p.symptoms}, Prescription: {p.prescription_text}") 