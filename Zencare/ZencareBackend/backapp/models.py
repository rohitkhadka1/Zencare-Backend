from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
    )

    PROFESSION_CHOICES = (
        ('general', 'General Physician'),
        ('dentist', 'Dentist'),
        ('dermatologist', 'Dermatologist'),
        ('ophthalmologist', 'Ophthalmologist'),
        ('pediatrician', 'Pediatrician'),
        ('psychiatrist', 'Psychiatrist'),
        ('other', 'Other'),
    )

    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='patient')
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if self.user_type == 'doctor' and not self.profession:
            raise ValueError("Profession is required for doctors")
        super().save(*args, **kwargs)
        
        # Assign appropriate group based on user type
        if self.user_type == 'doctor':
            doctor_group, _ = Group.objects.get_or_create(name='Doctors')
            self.groups.add(doctor_group)
        elif self.user_type == 'patient':
            patient_group, _ = Group.objects.get_or_create(name='Patients')
            self.groups.add(patient_group)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']