from django.urls import path, include
from .views import UserRegistrationView, UserLoginView, HomeView

app_name = 'backapp'

urlpatterns = [
    path("", HomeView.as_view(), name='home'),
    path("accounts/", include("django.contrib.auth.urls")),
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
]