from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from core.api_utils import throttled_token_obtain_pair_view
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from patients.api_views import PatientViewSet
from staff.api_views import StaffViewSet
from appointments.api_views import AppointmentViewSet
from billing.api_views import InvoiceViewSet
from integration.api_views import ExternalIntegrationViewSet
from laboratory.api_views import LabTestViewSet
from pharmacy.api_views import PrescriptionViewSet
from hospital.api_views import WardViewSet, RoomViewSet
from inventory.api_views import InventoryItemViewSet
from surgery.api_views import SurgeryViewSet
from care_monitoring.api_views import PatientCareViewSet
from core.views import homepage, health_check

api_router = DefaultRouter()
api_router.register(r"patients", PatientViewSet, basename="patient")
api_router.register(r"staff", StaffViewSet, basename="staff")
api_router.register(r"appointments", AppointmentViewSet, basename="appointment")
api_router.register(r"invoices", InvoiceViewSet, basename="invoice")
api_router.register(r"integrations", ExternalIntegrationViewSet, basename="integration")
api_router.register(r"lab-tests", LabTestViewSet, basename="labtest")
api_router.register(r"prescriptions", PrescriptionViewSet, basename="prescription")
api_router.register(r"wards", WardViewSet, basename="ward")
api_router.register(r"rooms", RoomViewSet, basename="room")
api_router.register(r"inventory", InventoryItemViewSet, basename="inventory")
api_router.register(r"surgeries", SurgeryViewSet, basename="surgery")
api_router.register(r"care-monitoring", PatientCareViewSet, basename="care-monitoring")

urlpatterns = [
    path("", homepage, name="home"),
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("api/v1/", include(api_router.urls)),
    path("api/v1/token/", throttled_token_obtain_pair_view(), name="token_obtain_pair"),
    path("api/v1/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/v1/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
    # All app URLs are namespaced. Use {% url 'app_name:view_name' %} in templates.
    path("", include("core.urls")),
    path("", include("patients.urls")),
    path("", include("staff.urls")),
    path("", include("appointments.urls")),
    path("", include(("billing.urls", "billing"))),
    path("", include("inventory.urls")),
    path("", include("laboratory.urls")),
    path("", include("pharmacy.urls")),
    path("hospital/", include(("hospital.urls", "hospital"))),
    path("", include("reporting.urls")),
    path("", include("integration.urls")),
    path("", include("surgery.urls")),
    path("", include("medical_records.urls")),
    path("", include("notifications.urls")),
    path("", include(("care_monitoring.urls", "care_monitoring"))),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
