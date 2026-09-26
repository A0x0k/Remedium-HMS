"""Tests for pharmacy app."""

import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.test import Client
from rest_framework import status
from pharmacy.models import Prescription
from pharmacy.openfda_service import search_drug_label, search_adverse_events
from patients.models import Patient
from staff.models import Staff
from django.contrib.auth.models import User


@pytest.mark.django_db
class TestPrescriptionModel:
    """Test Prescription model."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_PHARM",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_doctor(self):
        return Staff.objects.create(
            staff_id="DOC_PHARM",
            first_name="Dr. Test",
            last_name="Doctor",
            role="DOCTOR",
        )

    def test_create_prescription(self):
        patient = self._create_patient()
        doctor = self._create_doctor()
        rx = Prescription.objects.create(
            patient=patient,
            drug_name="Amoxicillin",
            dosage="500mg",
            frequency="3 times daily",
            prescribed_by=doctor,
        )
        assert rx.pk is not None
        assert str(rx) == "Amoxicillin for PAT_PHARM - Test Patient"

    def test_prescription_auto_date(self):
        """Test prescribed_date is auto-set."""
        patient = self._create_patient()
        rx = Prescription(
            patient=patient,
            drug_name="Test Drug",
            dosage="100mg",
            frequency="Daily",
        )
        rx.save()
        assert rx.prescribed_date is not None


@pytest.mark.django_db
class TestOpenFDAService:
    """Test OpenFDA API service functions."""

    @patch("pharmacy.openfda_service.requests.get")
    def test_search_drug_label_success(self, mock_get):
        """Test successful drug label search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "openfda": {
                        "generic_name": ["AMOXICILLIN"],
                        "brand_name": ["AMOXIL"],
                        "manufacturer_name": ["Test Pharma"],
                        "route": ["ORAL"],
                        "substance_name": ["AMOXICILLIN"],
                        "product_type": ["HUMAN PRESCRIPTION DRUG"],
                    },
                    "warnings_and_cautions": ["Use with caution."],
                    "adverse_reactions": ["Nausea, diarrhea."],
                    "dosage_and_administration": ["Take as directed."],
                    "drug_interactions": ["None known."],
                    "indications_and_usage": ["Bacterial infections."],
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_drug_label("Amoxicillin")
        assert result["generic_name"] == "AMOXICILLIN"
        assert result["brand_name"] == "AMOXIL"
        assert result["manufacturer"] == "Test Pharma"
        assert "ORAL" in result["route"]

    @patch("pharmacy.openfda_service.requests.get")
    def test_search_drug_label_not_found(self, mock_get):
        """Test drug not found returns error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_drug_label("NonExistentDrug")
        assert "error" in result

    @patch("pharmacy.openfda_service.requests.get")
    def test_search_drug_label_api_error(self, mock_get):
        """Test API failure returns error."""
        import requests as req
        from django.core.cache import cache

        cache.clear()  # Clear cache to avoid stale results
        mock_get.side_effect = req.RequestException("API down")

        result = search_drug_label("FailingDrug123")
        assert "error" in result

    @patch("pharmacy.openfda_service.requests.get")
    def test_search_adverse_events(self, mock_get):
        """Test adverse event search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"term": "Nausea", "count": 150},
                {"term": "Headache", "count": 80},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = search_adverse_events("Amoxicillin")
        assert result["drug_name"] == "Amoxicillin"
        assert len(result["top_adverse_reactions"]) == 2
        assert result["total_reports"] == 230


@pytest.mark.django_db
class TestPrescriptionAPIWithOpenFDA:
    """Test Prescription API with OpenFDA endpoints."""

    def _create_user(self):
        return User.objects.create_user(
            "pharm@test.com", "pharm@test.com", "pharmpass", is_staff=True
        )

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_API_PHARM",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_doctor(self):
        return Staff.objects.create(
            staff_id="DOC_PHARM_API",
            first_name="Dr.",
            last_name="Test",
            role="DOCTOR",
        )

    @patch("pharmacy.openfda_service.requests.get")
    def test_drug_info_endpoint(self, mock_get, api_client):
        """Test /api/v1/prescriptions/drug-info/ returns drug data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "openfda": {
                        "generic_name": ["IBUPROFEN"],
                        "brand_name": ["ADVIL"],
                        "manufacturer_name": ["Pfizer"],
                        "route": ["ORAL"],
                        "substance_name": ["IBUPROFEN"],
                        "product_type": ["HUMAN PRESCRIPTION DRUG"],
                    },
                    "warnings_and_cautions": ["Take with food."],
                    "adverse_reactions": ["Stomach upset."],
                    "dosage_and_administration": ["200mg every 6 hours."],
                    "drug_interactions": ["Blood thinners."],
                    "indications_and_usage": ["Pain relief."],
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        user = self._create_user()
        api_client.force_authenticate(user=user)
        response = api_client.get(
            "/api/v1/prescriptions/drug-info/", {"q": "Ibuprofen"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["generic_name"] == "IBUPROFEN"
        assert response.data["brand_name"] == "ADVIL"

    def test_drug_info_missing_query(self, api_client):
        """Test drug-info returns 400 without query parameter."""
        user = self._create_user()
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/v1/prescriptions/drug-info/")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("pharmacy.openfda_service.requests.get")
    def test_adverse_events_endpoint(self, mock_get, api_client):
        """Test /api/v1/prescriptions/adverse-events/ returns data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"term": "Dizziness", "count": 50},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        user = self._create_user()
        api_client.force_authenticate(user=user)
        response = api_client.get(
            "/api/v1/prescriptions/adverse-events/", {"q": "Aspirin"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_reports"] == 50


@pytest.mark.django_db
class TestPrescriptionViews:
    """Template rendering tests for Prescription views."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_RXV",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_doctor(self):
        return Staff.objects.create(
            staff_id="DOC_RXV",
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

    def test_list_requires_permission(self):
        user = User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("prescription_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_list_with_permission(self):
        client = self._login_with_permission("permuser", "pharmacy_view_prescription")
        url = reverse("prescription_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "prescriptions" in response.context

    def test_create_requires_permission(self):
        user = User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("prescription_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_create_with_permission(self):
        self._create_patient()
        self._create_doctor()
        client = self._login_with_permission("permuser", "pharmacy_add_prescription")
        url = reverse("prescription_create")
        response = client.get(url)
        assert response.status_code == 200
