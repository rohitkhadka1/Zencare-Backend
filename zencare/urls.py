"""
URL configuration for ZencareBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from admin_customization.admin import zencare_admin  # Import the custom admin site
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', RedirectView.as_view(url='/api/v1/')),  # Redirect root URL to API homepage
    path('admin/', zencare_admin.urls),  # Use the custom admin site
    path('api/v1/', include('backapp.urls')),
    path('api/v1/appointment/', include('appointment.urls')),
    path('api/v1/', include('notifications.urls')),  # Include notifications URLs
    # Password reset URLs - with CSRF exemption for API access
    path('api/v1/auth/password_reset/', csrf_exempt(auth_views.PasswordResetView.as_view()), name='password_reset'),
    path('api/v1/auth/password_reset/done/', csrf_exempt(auth_views.PasswordResetDoneView.as_view()), name='password_reset_done'),
    path('api/v1/auth/reset/<uidb64>/<token>/', csrf_exempt(auth_views.PasswordResetConfirmView.as_view()), name='password_reset_confirm'),
    path('api/v1/auth/reset/done/', csrf_exempt(auth_views.PasswordResetCompleteView.as_view()), name='password_reset_complete'),
] 

# Serve media files in all environments
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files - typically handled by WhiteNoise in production
urlpatterns += staticfiles_urlpatterns()

# Explicit static file serving as a fallback
urlpatterns += [
    path('static/<path:path>', serve, {'document_root': settings.STATIC_ROOT}),
]
