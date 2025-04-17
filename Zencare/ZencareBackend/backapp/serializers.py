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
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, default='patient')
    profession = serializers.ChoiceField(choices=User.PROFESSION_CHOICES, required=False, allow_null=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 
                 'user_type', 'profession', 'phone_number', 'date_of_birth', 'address')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Validate profession based on user_type
        if attrs['user_type'] == 'doctor' and not attrs.get('profession'):
            raise serializers.ValidationError({"profession": "Profession is required for doctors."})
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
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
    
    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'profession', 'phone_number', 'address')
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_type_display = serializers.SerializerMethodField()
    profession_display = serializers.SerializerMethodField()
    appointments = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'full_name', 'user_type', 'user_type_display',
            'profession', 'profession_display', 'phone_number', 
            'date_of_birth', 'address', 'is_verified', 'appointments'
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