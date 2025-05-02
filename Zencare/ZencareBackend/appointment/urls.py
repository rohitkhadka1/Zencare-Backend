from django.urls import path
from .views import (
    AppointmentCreateView,
    AppointmentListView,
    AppointmentDetailView,
    MedicalReportCreateView,
    MedicalReportListView,
    MedicalReportDetailView,
    PrescriptionCreateView,
    PrescriptionListView,
    PrescriptionDetailView,
    PendingAppointmentsView,
    LabTestsRequiredView,
    prescription_test_form
)

app_name = 'appointment'

urlpatterns = [
    path('', AppointmentListView.as_view(), name='appointment-list'),
    path('create/', AppointmentCreateView.as_view(), name='appointment-create'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('reports/', MedicalReportListView.as_view(), name='medical-report-list'),
    path('reports/create/', MedicalReportCreateView.as_view(), name='medical-report-create'),
    path('reports/<int:pk>/', MedicalReportDetailView.as_view(), name='medical-report-detail'),
    path('prescriptions/', PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/create/', PrescriptionCreateView.as_view(), name='prescription-create'),
    path('prescriptions/test/', prescription_test_form, name='prescription-test-form'),
    path('prescriptions/<int:pk>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('pending/', PendingAppointmentsView.as_view(), name='pending-appointments'),
    path('lab-tests-required/', LabTestsRequiredView.as_view(), name='lab-tests-required'),
]