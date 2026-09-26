"""Tests for appointments app."""

import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.test import Client
from appointments.models import Appointment
from patients.models import Patient
from staff.models import Staff


@pytest.mark.django_db
class TestAppointmentModel:
    """Test Appointment model."""

    def _create_patient(self):
        """Helper to create a test patient."""
        return Patient.objects.create(
            unique_id="PAT_APPT",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_doctor(self):
        """Helper to create a test doctor."""
        return Staff.objects.create(
            staff_id="DOC001",
            first_name="Dr. Test",
            last_name="Doctor",
            role="Doctor",
        )

    def test_create_appointment(self):
        """Test basic appointment creation."""
        patient = self._create_patient()
        doctor = self._create_doctor()
        appt = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now() + timedelta(days=1),
            reason="Checkup",
        )
        assert appt.pk is not None
        assert appt.status == "Scheduled"

    def test_appointment_str(self):
        """Test string representation."""
        patient = self._create_patient()
        doctor = self._create_doctor()
        appt = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now() + timedelta(days=1),
        )
        assert str(appt)

    def test_past_appointment_raises_error(self):
        """Test creating appointment in the past raises error."""
        patient = self._create_patient()
        doctor = self._create_doctor()
        appt = Appointment(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now() - timedelta(days=1),
        )
        with pytest.raises(ValidationError):
            appt.full_clean()

    def test_status_choices(self):
        """Test status field accepts valid choices."""
        patient = self._create_patient()
        doctor = self._create_doctor()
        for status in ["Scheduled", "Completed", "Cancelled"]:
            appt = Appointment(
                patient=patient,
                doctor=doctor,
                appointment_date=timezone.now() + timedelta(days=1),
                status=status,
            )
            appt.full_clean()  # Should not raise


@pytest.mark.django_db
class TestAppointmentViews:
    """Template rendering tests for Appointment views."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_APPTV",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_doctor(self):
        return Staff.objects.create(
            staff_id="DOC_TST",
            first_name="Dr. Test",
            last_name="Doctor",
            role="DOCTOR",
        )

    def _login_with_permission(self, username, codename):
        client = Client()
        user = User.objects.create_user(username=username, password="pass")
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
        client.login(username=username, password="pass")
        return client

    def _create_appointment(self):
        patient = self._create_patient()
        doctor = self._create_doctor()
        return Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.now() + timedelta(days=1),
            reason="Checkup",
        )

    def test_list_requires_permission(self):
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("appointment_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_list_with_permission(self):
        client = self._login_with_permission("permuser", "appointments_view_appointment")
        url = reverse("appointment_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "appointments" in response.context

    def test_detail_requires_permission(self):
        appt = self._create_appointment()
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("appointment_detail", kwargs={"pk": appt.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_detail_with_permission(self):
        appt = self._create_appointment()
        client = self._login_with_permission("permuser", "appointments_view_appointment")
        url = reverse("appointment_detail", kwargs={"pk": appt.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["appointment"].pk == appt.pk

    def test_create_requires_permission(self):
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("appointment_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_create_with_permission(self):
        self._create_patient()
        self._create_doctor()
        client = self._login_with_permission("permuser", "appointments_add_appointment")
        url = reverse("appointment_create")
        response = client.get(url)
        assert response.status_code == 200

    def test_queue_tracker_with_permission(self):
        client = self._login_with_permission("permuser", "appointments_view_appointment")
        url = reverse("queue_tracker")
        response = client.get(url)
        assert response.status_code == 200
