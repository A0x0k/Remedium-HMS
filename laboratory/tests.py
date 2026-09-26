"""Tests for laboratory app."""

import pytest
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.test import Client
from laboratory.models import LabTest
from patients.models import Patient
from hospital.models import HospitalService


@pytest.mark.django_db
class TestLabTestModel:
    """Test LabTest model."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_LAB",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_service(self):
        return HospitalService.objects.create(
            name="Blood Analysis", category="LABORATORY", base_price=50.00
        )

    def test_create_lab_test(self):
        patient = self._create_patient()
        service = self._create_service()
        test = LabTest.objects.create(
            patient=patient,
            service=service,
            test_name="Blood Test",
            status="Requested",
        )
        assert test.pk is not None
        assert test.status == "Requested"
        assert str(test) == "Blood Test for PAT_LAB - Test Patient"

    def test_lab_test_auto_requested_date(self):
        """Test requested_date is auto-set."""
        patient = self._create_patient()
        service = self._create_service()
        test = LabTest(patient=patient, service=service, test_name="X-Ray")
        test.save()
        assert test.requested_date is not None

    def test_lab_test_status_choices(self):
        """Test valid status values."""
        patient = self._create_patient()
        service = self._create_service()
        for status in ["Requested", "Completed", "Cancelled"]:
            test = LabTest(
                patient=patient,
                service=service,
                test_name=f"{status} Test",
                status=status,
            )
            test.full_clean()  # Should not raise


@pytest.mark.django_db
class TestLabTestViews:
    """Template rendering tests for LabTest views."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_LABV",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
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
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("labtest_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_list_with_permission(self):
        client = self._login_with_permission("permuser", "laboratory_view_labtest")
        url = reverse("labtest_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "lab_tests" in response.context

    def test_create_requires_permission(self):
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("labtest_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_create_with_permission(self):
        self._create_patient()
        client = self._login_with_permission("permuser", "laboratory_add_labtest")
        url = reverse("labtest_create")
        response = client.get(url)
        assert response.status_code == 200
