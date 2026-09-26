"""API integration tests for ViewSets."""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from patients.models import Patient
from staff.models import Staff
from appointments.models import Appointment
from billing.models import Invoice
from laboratory.models import LabTest
from pharmacy.models import Prescription
from django.contrib.auth.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        "admin@test.com", "admin@test.com", "adminpass123"
    )


@pytest.fixture
def doctor_user(db):
    user = User.objects.create_user("doctor@test.com", "doctor@test.com", "docpass123")
    Staff.objects.create(
        staff_id="DOC_API",
        first_name="Dr. Test",
        last_name="Doctor",
        role="DOCTOR",
        user=user,
    )
    return user


@pytest.fixture
def nurse_user(db):
    user = User.objects.create_user("nurse@test.com", "nurse@test.com", "nurpass123")
    Staff.objects.create(
        staff_id="NRS_API",
        first_name="Nurse",
        last_name="Test",
        role="NURSE",
        user=user,
    )
    return user


@pytest.fixture
def receptionist_user(db):
    user = User.objects.create_user(
        "reception@test.com", "reception@test.com", "recpass123"
    )
    Staff.objects.create(
        staff_id="REC_API",
        first_name="Reception",
        last_name="Test",
        role="RECEPTIONIST",
        user=user,
    )
    return user


@pytest.fixture
def patient(db):
    return Patient.objects.create(
        unique_id="PAT_API",
        first_name="API",
        last_name="Patient",
        date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
        gender="M",
    )


@pytest.mark.django_db
class TestPatientAPI:
    """Test Patient API ViewSet."""

    def test_unauthenticated_cannot_access(self, api_client):
        response = api_client.get("/api/v1/patients/")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_receptionist_cannot_view_patients(
        self, api_client, receptionist_user, patient
    ):
        api_client.force_authenticate(user=receptionist_user)
        response = api_client.get("/api/v1/patients/")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_nurse_can_view_patients(self, api_client, nurse_user, patient):
        api_client.force_authenticate(user=nurse_user)
        response = api_client.get("/api/v1/patients/")
        # Nurse has staff_profile with role NURSE which is in MEDICAL_ROLES
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_doctor_can_view_patients(self, api_client, doctor_user, patient):
        # Debug: verify staff_profile exists
        assert hasattr(doctor_user, "staff_profile")
        assert doctor_user.staff_profile.role == "DOCTOR"
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get("/api/v1/patients/")
        assert (
            response.status_code == status.HTTP_200_OK
        ), f"Got {response.status_code}: {response.data}"

    def test_discharge_non_admitted_patient_fails(
        self, api_client, doctor_user, patient
    ):
        api_client.force_authenticate(user=doctor_user)
        response = api_client.post(f"/api/v1/patients/{patient.pk}/discharge/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "not currently admitted" in str(response.data).lower()


@pytest.mark.django_db
class TestAppointmentAPI:
    """Test Appointment API ViewSet."""

    def test_scheduled_appointments(self, api_client, doctor_user, patient):
        Appointment.objects.create(
            patient=patient,
            doctor=doctor_user.staff_profile,
            appointment_date=timezone.now() + timedelta(days=1),
            status="Scheduled",
        )
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get("/api/v1/appointments/scheduled/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_upcoming_appointments(self, api_client, doctor_user, patient):
        Appointment.objects.create(
            patient=patient,
            doctor=doctor_user.staff_profile,
            appointment_date=timezone.now() + timedelta(days=1),
            status="Scheduled",
        )
        api_client.force_authenticate(user=doctor_user)
        response = api_client.get("/api/v1/appointments/upcoming/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestInvoiceAPI:
    """Test Invoice API ViewSet."""

    def test_unpaid_invoices(self, api_client, admin_user, patient):
        Invoice.objects.create(
            patient=patient,
            total_amount=100.00,
            paid=False,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/invoices/unpaid/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_mark_paid_creates_payment_record(self, api_client, admin_user, patient):
        invoice = Invoice.objects.create(
            patient=patient,
            total_amount=100.00,
            paid=False,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            f"/api/v1/invoices/{invoice.pk}/mark_paid/",
            {"amount": 100.00, "payment_method": "CASH"},
        )
        assert response.status_code == status.HTTP_200_OK
        invoice.refresh_from_db()
        assert invoice.paid is True
        assert invoice.payments.count() == 1

    def test_mark_already_paid_fails(self, api_client, admin_user, patient):
        invoice = Invoice.objects.create(
            patient=patient,
            total_amount=100.00,
            paid=True,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(f"/api/v1/invoices/{invoice.pk}/mark_paid/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAuthToken:
    """Test token auth endpoint with rate limiting."""

    def test_token_auth_works(self, api_client, admin_user):
        response = api_client.post(
            "/api/v1/token/", {"username": "admin@test.com", "password": "adminpass123"}
        )
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_invalid_credentials(self, api_client):
        response = api_client.post(
            "/api/v1/token/", {"username": "bad", "password": "wrong"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLabTestAPI:
    """Test LabTest API ViewSet."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_LAB_API",
            first_name="Lab",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def test_list_lab_tests(self, api_client, admin_user):
        patient = self._create_patient()
        LabTest.objects.create(
            patient=patient,
            test_name="Blood Test",
            status="Requested",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/lab-tests/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_lab_tests(self, api_client, admin_user):
        patient = self._create_patient()
        LabTest.objects.create(
            patient=patient,
            test_name="Blood Test",
            status="Requested",
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/lab-tests/", {"search": "Blood"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestPrescriptionAPI:
    """Test Prescription API ViewSet."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_PHARM_API",
            first_name="Pharm",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_doctor(self):
        return Staff.objects.create(
            staff_id="DOC_PHARM_API",
            first_name="Dr. Test",
            last_name="Doctor",
            role="DOCTOR",
        )

    def test_list_prescriptions(self, api_client, admin_user):
        patient = self._create_patient()
        doctor = self._create_doctor()
        Prescription.objects.create(
            patient=patient,
            drug_name="Amoxicillin",
            dosage="500mg",
            frequency="3 times daily",
            prescribed_by=doctor,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/prescriptions/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_search_prescriptions(self, api_client, admin_user):
        patient = self._create_patient()
        doctor = self._create_doctor()
        Prescription.objects.create(
            patient=patient,
            drug_name="Amoxicillin",
            dosage="500mg",
            frequency="3 times daily",
            prescribed_by=doctor,
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/prescriptions/", {"search": "Amoxicillin"})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


@pytest.mark.django_db
class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_schema_endpoint_accessible(self, api_client, admin_user):
        """Test OpenAPI schema endpoint returns valid schema."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == status.HTTP_200_OK
        assert "openapi" in response.data

    def test_swagger_ui_accessible(self, api_client):
        """Test Swagger UI page loads without auth."""
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == status.HTTP_200_OK

    def test_redoc_accessible(self, api_client):
        """Test ReDoc page loads without auth."""
        response = api_client.get("/api/v1/redoc/")
        assert response.status_code == status.HTTP_200_OK

    def test_schema_contains_all_endpoints(self, api_client, admin_user):
        """Test schema includes all expected API endpoints."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/schema/")
        paths = response.data.get("paths", {})
        assert any("patients" in p for p in paths)
        assert any("staff" in p for p in paths)
        assert any("appointments" in p for p in paths)
        assert any("invoices" in p for p in paths)
        assert any("lab-tests" in p for p in paths)
        assert any("prescriptions" in p for p in paths)

    def test_schema_has_proper_title(self, api_client, admin_user):
        """Test schema has proper metadata."""
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/schema/")
        assert (
            response.data["info"]["title"] == "Remedium Hospital Management System API"
        )
        assert response.data["info"]["version"] == "1.0.0"


@pytest.mark.django_db
class TestCoreViews:
    """Test core HTML views — homepage, health check, audit log."""

    def test_homepage_unauthenticated(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_homepage_authenticated(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get("/")
        assert response.status_code == 200
        assert b"Welcome" in response.content

    def test_health_check(self, client):
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_audit_log_requires_admin(self, client, doctor_user):
        client.force_login(doctor_user)
        response = client.get("/audit-log/")
        assert response.status_code in (302, 403)

    def test_audit_log_accessible_to_admin(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get("/audit-log/")
        assert response.status_code == 200

    def test_logout_redirects(self, client, admin_user):
        client.force_login(admin_user)
        response = client.post("/logout/")
        assert response.status_code == 302


@pytest.mark.django_db
class TestBillingAPIExtended:
    """Additional billing API coverage."""

    def test_overdue_invoices(self, api_client, admin_user, patient):
        from datetime import date, timedelta

        Invoice.objects.create(
            patient=patient,
            total_amount=200.00,
            paid=False,
            issue_date=date.today() - timedelta(days=30),
            due_date=date.today() - timedelta(days=10),
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/invoices/overdue/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_mark_paid_with_payment_method(self, api_client, admin_user, patient):
        invoice = Invoice.objects.create(
            patient=patient, total_amount=150.00, paid=False
        )
        api_client.force_authenticate(user=admin_user)
        response = api_client.post(
            f"/api/v1/invoices/{invoice.pk}/mark_paid/",
            {"amount": "150.00", "payment_method": "CARD", "transaction_id": "TXN123"},
            format="json",
        )
        assert response.status_code == 200
        invoice.refresh_from_db()
        assert invoice.paid is True
        payment = invoice.payments.first()
        assert payment.payment_method == "CARD"
        assert payment.transaction_id == "TXN123"

    def test_invoice_search(self, api_client, admin_user, patient):
        Invoice.objects.create(patient=patient, total_amount=50.00)
        api_client.force_authenticate(user=admin_user)
        response = api_client.get("/api/v1/invoices/", {"search": patient.unique_id})
        assert response.status_code == 200
        assert response.data["count"] >= 1
