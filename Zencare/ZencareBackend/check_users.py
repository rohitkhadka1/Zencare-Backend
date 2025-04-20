#!/usr/bin/env python
# Quick script to check users in database

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ZencareBackend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("All users in database:")
for user in User.objects.all():
    print(f"ID: {user.id}, Email: {user.email}, Name: {user.first_name} {user.last_name}, Type: {user.user_type}")

print("\nDoctors only:")
doctors = User.objects.filter(user_type='doctor')
if doctors.exists():
    for doctor in doctors:
        print(f"ID: {doctor.id}, Name: {doctor.first_name} {doctor.last_name}")
else:
    print("No doctors found in database!")

print("\nCreating a test doctor if none exists:")
if not doctors.exists():
    doctor = User.objects.create_user(
        email="doctor@example.com",
        password="password123",
        first_name="John",
        last_name="Doe",
        user_type="doctor",
        profession="general",
        is_active=True
    )
    print(f"Created test doctor with ID: {doctor.id}") 