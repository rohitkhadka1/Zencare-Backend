from django.urls import path
from .views import (
    HomeView,
    UserRegistrationView,
    UserLoginView,
    DoctorListView,
    CustomTokenRefreshView
)

app_name = 'backapp'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('doctors/', DoctorListView.as_view(), name='doctor-list'),
]