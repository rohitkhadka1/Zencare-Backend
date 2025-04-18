from django.urls import path
from .views import (
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    MedicalReportCreateView,
    MedicalReportListView,
    MedicalReportDetailView
)

app_name = 'appointment'

urlpatterns = [
    path('', AppointmentListView.as_view(), name='appointment-list'),
    path('create/', AppointmentCreateView.as_view(), name='appointment-create'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('reports/', MedicalReportListView.as_view(), name='medical-report-list'),
    path('reports/create/', MedicalReportCreateView.as_view(), name='medical-report-create'),
    path('reports/<int:pk>/', MedicalReportDetailView.as_view(), name='medical-report-detail'),
]