from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_profile_completed', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('patient', 'Patient'),
        ('doctor', 'Doctor'),
        ('lab_technician', 'Lab Technician'),
        ('admin', 'Admin'),
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
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    username = None  # Remove username field
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='patient')
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES, blank=True, null=True)
    
    # Basic profile fields
    phone_number = models.CharField(max_length=15, blank=True)
    phone_number_2 = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    
    is_verified = models.BooleanField(default=False)
    is_profile_completed = models.BooleanField(default=False)
    
    # Doctor specific fields
    experience_years = models.PositiveIntegerField(null=True, blank=True, help_text="Years of experience for doctors")
    work_experience = models.TextField(blank=True, help_text="Previous work places and experience details")
    education = models.TextField(blank=True, help_text="Education background and qualifications")
    training = models.TextField(blank=True, help_text="Additional training and certifications")
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Consultation fee in USD")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if self.user_type == 'doctor' and not self.profession and not kwargs.get('skip_validation', False):
            raise ValueError("Profession is required for doctors")
            
        # Check if profile is completed for patients
        if self.user_type == 'patient':
            if (self.first_name and self.last_name and self.phone_number and 
                self.date_of_birth and self.address and self.city and 
                self.state and self.country and self.gender):
                self.is_profile_completed = True
                
        # Remove skip_validation if it exists
        if 'skip_validation' in kwargs:
            kwargs.pop('skip_validation')
            
        super().save(*args, **kwargs)
        
        # Assign appropriate group based on user type
        if self.user_type == 'doctor':
            doctor_group, _ = Group.objects.get_or_create(name='Doctors')
            self.groups.add(doctor_group)
        elif self.user_type == 'patient':
            patient_group, _ = Group.objects.get_or_create(name='Patients')
            self.groups.add(patient_group)
        elif self.user_type == 'lab_technician':
            lab_tech_group, _ = Group.objects.get_or_create(name='Lab Technicians')
            self.groups.add(lab_tech_group)
        elif self.user_type == 'admin':
            admin_group, _ = Group.objects.get_or_create(name='Admins')
            self.groups.add(admin_group)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-created_at']