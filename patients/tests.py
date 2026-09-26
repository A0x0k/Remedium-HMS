"""Tests for patients app."""

import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.test import Client
from patients.models import Patient


@pytest.mark.django_db
class TestPatientModel:
    """Test Patient model."""

    def test_create_patient(self):
        """Test basic patient creation."""
        patient = Patient.objects.create(
            unique_id="PAT001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            gender="M",
        )
        assert patient.pk is not None
        assert str(patient) == "PAT001 - John Doe"

    def test_full_name_property(self):
        """Test full_name property."""
        patient = Patient(
            unique_id="PAT002",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1985, 5, 15),
            gender="F",
        )
        assert patient.full_name == "Jane Smith"

    def test_age_property(self):
        """Test age calculation."""
        birth_date = date.today().replace(year=date.today().year - 30)
        patient = Patient(
            unique_id="PAT003",
            first_name="Test",
            last_name="User",
            date_of_birth=birth_date,
            gender="O",
        )
        assert patient.age == 30

    def test_age_property_no_dob(self):
        """Test age returns None when DOB not set."""
        patient = Patient(
            unique_id="PAT004",
            first_name="Test",
            last_name="User",
            date_of_birth=None,
            gender="O",
        )
        assert patient.age is None

    def test_is_admitted_property(self):
        """Test is_admitted property."""
        from django.utils import timezone

        patient = Patient(
            unique_id="PAT005",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            admission_date=timezone.now() - timedelta(days=1),
            discharge_date=None,
        )
        assert patient.is_admitted is True

    def test_is_admitted_discharged(self):
        """Test is_admitted returns False after discharge."""
        from django.utils import timezone

        patient = Patient(
            unique_id="PAT006",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            admission_date=timezone.now() - timedelta(days=2),
            discharge_date=timezone.now() - timedelta(days=1),
        )
        assert patient.is_admitted is False

    def test_phone_invalid_format_rejected(self):
        """Phone numbers with dashes are invalid and must be rejected."""
        from django.core.exceptions import ValidationError

        patient = Patient(
            unique_id="PAT007",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            phone="555-123-4567",
        )
        with pytest.raises(ValidationError):
            patient.full_clean()

    def test_valid_phone_with_plus(self):
        """Test valid phone with country code."""
        patient = Patient(
            unique_id="PAT008",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            phone="+12345678901",
        )
        patient.full_clean()  # Should not raise

    def test_invalid_phone_too_short(self):
        """Test invalid phone number too short."""
        patient = Patient(
            unique_id="PAT009",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            phone="+123",
        )
        with pytest.raises(ValidationError):
            patient.full_clean()

    def test_date_of_birth_in_future_raises_error(self):
        """Test DOB in future raises validation error."""
        patient = Patient(
            unique_id="PAT010",
            first_name="Test",
            last_name="User",
            date_of_birth=date.today() + timedelta(days=1),
            gender="M",
        )
        with pytest.raises(ValidationError):
            patient.full_clean()

    def test_discharge_before_admission_raises_error(self):
        """Test discharge before admission raises constraint error."""
        from django.utils import timezone

        patient = Patient(
            unique_id="PAT011",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            admission_date=timezone.now() + timedelta(days=1),
            discharge_date=timezone.now(),
        )
        with pytest.raises(ValidationError):
            patient.full_clean()

    def test_gender_normalization(self):
        """Test gender normalization from display value."""
        patient = Patient(
            unique_id="PAT012",
            first_name="Test",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="Male",
        )
        patient.save()
        assert patient.gender == "M"

    def test_unique_id_must_be_unique(self):
        """Test unique_id constraint."""
        Patient.objects.create(
            unique_id="DUP001",
            first_name="First",
            last_name="User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
        )
        with pytest.raises(Exception):  # IntegrityError
            Patient.objects.create(
                unique_id="DUP001",
                first_name="Second",
                last_name="User",
                date_of_birth=date(1990, 1, 1),
                gender="M",
            )


@pytest.mark.django_db
class TestPatientViews:
    """Template rendering tests for Patient views."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_VW",
            first_name="Test",
            last_name="Patient",
            date_of_birth=date(1990, 1, 1),
            gender="M",
        )

    def _login_with_permission(self, username, codename):
        client = Client()
        user = User.objects.create_user(username=username, password="pass")
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
        client.login(username=username, password="pass")
        return client

    def test_list_requires_permission(self):
        user = User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("patient_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_list_with_permission(self):
        client = self._login_with_permission("permuser", "patients_view_patient")
        url = reverse("patient_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "patients" in response.context

    def test_detail_requires_permission(self):
        patient = self._create_patient()
        user = User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("patient_detail", kwargs={"pk": patient.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_detail_with_permission(self):
        patient = self._create_patient()
        client = self._login_with_permission("permuser", "patients_view_patient")
        url = reverse("patient_detail", kwargs={"pk": patient.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["patient"].pk == patient.pk

    def test_create_requires_permission(self):
        user = User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("patient_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_create_with_permission(self):
        client = self._login_with_permission("permuser", "patients_add_patient")
        url = reverse("patient_create")
        response = client.get(url)
        assert response.status_code == 200

    def test_history_with_permission(self):
        patient = self._create_patient()
        client = self._login_with_permission("permuser", "patients_view_patient")
        url = reverse("patient_history", kwargs={"pk": patient.pk})
        response = client.get(url)
        assert response.status_code == 200
