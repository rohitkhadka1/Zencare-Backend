from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserRegistrationSerializer, UserLoginSerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.

class HomeView(APIView):
    def get(self, request):
        return Response({
            'message': 'Welcome to Zencare API',
            'endpoints': {
                'register': '/auth/register/',
                'login': '/auth/login/',
                'admin': '/admin/'
            }
        })

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer

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
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'error': 'An error occurred during registration',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserLoginView(APIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                user = authenticate(
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password']
                )
                if user:
                    refresh = RefreshToken.for_user(user)
                    logger.info(f"User logged in successfully: {user.email}")
                    return Response({
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    })
                logger.warning(f"Failed login attempt for email: {serializer.validated_data['email']}")
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            logger.error(f"Login validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                'error': 'An error occurred during login',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
