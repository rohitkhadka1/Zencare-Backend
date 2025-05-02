from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from appointment.models import Appointment
from appointment.serializers import AppointmentSerializer

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    # Only these fields required for initial registration
    email = serializers.EmailField(required=True)
    
    # Other fields are not required during initial registration
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 'user_type')
        extra_kwargs = {
            'user_type': {'default': 'patient', 'read_only': True},  # Force patient user type for registration
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
            
        # Ensure only patients can self-register
        if 'user_type' in attrs and attrs['user_type'] != 'patient':
            raise serializers.ValidationError({"user_type": "Only patients can self-register"})
        
        # Force user_type to patient for self-registration
        attrs['user_type'] = 'patient'
        attrs['is_profile_completed'] = False
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)


class CompleteProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'phone_number', 'phone_number_2',
            'date_of_birth', 'address', 'city', 'state', 'country', 'gender'
        )
        
    def validate(self, attrs):
        # Ensure all required fields are provided
        required_fields = ['first_name', 'last_name', 'phone_number', 
                          'date_of_birth', 'address', 'city', 'state', 
                          'country', 'gender']
        
        for field in required_fields:
            if field not in attrs or not attrs[field]:
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required to complete your profile"})
        
        return attrs
        
    def update(self, instance, validated_data):
        # Update the user instance with profile details
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Set profile as completed
        instance.is_profile_completed = True
        instance.save()
        
        return instance


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        # Special case for admin login with hardcoded credentials
        if email == 'zencare@admin.com' and password == 'admin@123':
            try:
                # Try to get existing admin user
                user = User.objects.filter(email=email).first()
                
                if not user:
                    # Create admin user if it doesn't exist
                    user = User.objects.create_user(
                        email=email,
                        password=password,
                        user_type='admin',
                        first_name='Admin',
                        last_name='User',
                        is_staff=True,
                        is_superuser=True,
                        is_active=True,
                        is_profile_completed=True
                    )
                elif not user.check_password(password):
                    # Update password if it's changed
                    user.set_password(password)
                    user.save()
                
                attrs['user'] = user
                return attrs
            except Exception as e:
                raise serializers.ValidationError(f"Admin login setup error: {str(e)}")
                
        if email and password:
            user = User.objects.filter(email=email).first()
            if user and user.check_password(password):
                if not user.is_active:
                    raise serializers.ValidationError("User account is disabled.")
                attrs['user'] = user
                return attrs
            raise serializers.ValidationError("Unable to log in with provided credentials.")
        raise serializers.ValidationError("Must include 'email' and 'password'.")


class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    profession_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'profession', 'profession_display', 
                 'phone_number', 'address', 'experience_years', 'work_experience', 
                 'education', 'training', 'consultation_fee')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
        
    def get_profession_display(self, obj):
        if obj.profession:
            return dict(User.PROFESSION_CHOICES).get(obj.profession)
        return None


class CreateStaffUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'first_name', 'last_name', 'user_type',
            'profession', 'phone_number', 'date_of_birth', 'address',
            'city', 'state', 'country', 'gender', 'experience_years',
            'work_experience', 'education', 'training', 'consultation_fee'
        )
        
    def validate(self, attrs):
        # Only admins can create staff users
        if self.context['request'].user.user_type != 'admin' and not self.context['request'].user.is_superuser:
            raise serializers.ValidationError("Only administrators can create staff users")
            
        # Validate user type
        user_type = attrs.get('user_type')
        if user_type not in ['doctor', 'lab_technician']:
            raise serializers.ValidationError({"user_type": "Staff users must be doctors or lab technicians"})
            
        # Validate profession for doctors
        if user_type == 'doctor' and not attrs.get('profession'):
            raise serializers.ValidationError({"profession": "Profession is required for doctors"})
            
        return attrs
        
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data, is_profile_completed=True, is_verified=True)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_type_display = serializers.SerializerMethodField()
    profession_display = serializers.SerializerMethodField()
    appointments = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'user_type', 'user_type_display',
            'profession', 'profession_display', 'phone_number', 'phone_number_2',
            'date_of_birth', 'address', 'city', 'state', 'country', 'gender',
            'is_verified', 'is_profile_completed', 'appointments',
            'experience_years', 'work_experience', 'education', 'training', 
            'consultation_fee'
        )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_user_type_display(self, obj):
        return dict(User.USER_TYPE_CHOICES).get(obj.user_type)
    
    def get_profession_display(self, obj):
        if obj.profession:
            return dict(User.PROFESSION_CHOICES).get(obj.profession)
        return None
    
    def get_appointments(self, obj):
        # Only include appointments for patients and doctors
        if obj.user_type == 'patient':
            appointments = Appointment.objects.filter(patient=obj)
        elif obj.user_type == 'doctor':
            appointments = Appointment.objects.filter(doctor=obj)
        else:
            return []
        
        return AppointmentSerializer(appointments, many=True).data


class ProfileDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing just the profile details that users enter during first login
    """
    full_name = serializers.SerializerMethodField()
    gender_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'first_name', 'last_name', 
            'phone_number', 'phone_number_2', 'date_of_birth', 
            'address', 'city', 'state', 'country', 
            'gender', 'gender_display', 'is_profile_completed'
        )
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_gender_display(self, obj):
        if obj.gender:
            return dict(User.GENDER_CHOICES).get(obj.gender)
        return None