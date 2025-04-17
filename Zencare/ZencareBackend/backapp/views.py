from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer, DoctorListSerializer
import logging
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from django.core.exceptions import ValidationError
from rest_framework.filters import SearchFilter, OrderingFilter

logger = logging.getLogger(__name__)

User = get_user_model()

# Create your views here.

class HomeView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'message': 'Welcome to Zencare API',
            'endpoints': {
                'register': '/auth/register/',
                'login': '/auth/login/',
                'doctors': '/doctors/',
                'token_refresh': '/auth/token/refresh/',
                'appointments': {
                    'list': '/appointment/',
                    'create': '/appointment/create/',
                    'detail': '/appointment/<id>/'
                }
            }
        })

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                logger.info(f"User registered successfully: {user.email}")
                return Response({
                    'user': serializer.data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_201_CREATED)
            logger.error(f"Registration validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.error(f"Registration validation error: {str(e)}")
            return Response({
                'error': 'Validation error',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'error': 'An error occurred during registration',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = serializer.validated_data['user']
                refresh = RefreshToken.for_user(user)
                logger.info(f"User logged in successfully: {user.email}")
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })
            logger.error(f"Login validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                'error': 'An error occurred during login',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DoctorListView(generics.ListAPIView):
    serializer_class = DoctorListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'profession', 'address']
    ordering_fields = ['first_name', 'last_name', 'profession']

    def get_queryset(self):
        queryset = User.objects.filter(user_type='doctor', is_active=True)
        
        # Filter by profession if provided
        profession = self.request.query_params.get('profession', None)
        if profession:
            queryset = queryset.filter(profession=profession)
            
        return queryset

class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]