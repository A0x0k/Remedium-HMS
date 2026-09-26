"""Tests for medical_records app."""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Permission
from django.test import Client
from medical_records.models import PatientDocument, Encounter
from patients.models import Patient


@pytest.mark.django_db
class TestPatientDocumentModel:
    """Test PatientDocument model."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_DOC",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def _create_pdf_file(self):
        """Create a minimal PDF-like file for testing."""
        content = b"%PDF-1.4 dummy content"
        return SimpleUploadedFile(
            "test_document.pdf", content, content_type="application/pdf"
        )

    def test_create_patient_document(self):
        patient = self._create_patient()
        pdf_file = self._create_pdf_file()
        doc = PatientDocument.objects.create(
            patient=patient,
            document_type="LAB_REPORT",
            title="Blood Test Results",
            file=pdf_file,
        )
        assert doc.pk is not None
        assert doc.document_type == "LAB_REPORT"
        assert "Blood Test" in str(doc)

    def test_document_types(self):
        """Test valid document type choices."""
        patient = self._create_patient()
        pdf_file = self._create_pdf_file()
        for doc_type in [
            "LAB_REPORT",
            "XRAY",
            "MRI",
            "PRESCRIPTION",
            "INSURANCE",
            "OTHER",
        ]:
            doc = PatientDocument(
                patient=patient,
                document_type=doc_type,
                title=f"{doc_type} Document",
                file=pdf_file,
            )
            doc.full_clean()  # Should not raise

    def test_invalid_file_extension_rejected(self):
        """Test that .doc/.docx files are rejected."""
        patient = self._create_patient()
        doc_file = SimpleUploadedFile(
            "test.docx",
            b"mock word content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        doc = PatientDocument(
            patient=patient,
            document_type="OTHER",
            title="Invalid Doc",
            file=doc_file,
        )
        with pytest.raises(ValidationError):
            doc.full_clean()

    def test_create_encounter(self):
        """Test Encounter creation."""
        patient = self._create_patient()
        enc = Encounter.objects.create(
            patient=patient,
            encounter_type="AMBULATORY",
            reason_for_visit="Checkup",
        )
        assert enc.pk is not None
        assert enc.reason_for_visit == "Checkup"

    def test_encounter_detail_view_requires_permission(self):
        """Test encounter detail requires permission."""
        patient = self._create_patient()
        enc = Encounter.objects.create(
            patient=patient,
            encounter_type="AMBULATORY",
            reason_for_visit="Checkup",
        )
        user = User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("encounter_detail", kwargs={"pk": enc.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_encounter_detail_view_with_permission(self):
        """Test encounter detail loads with proper permission."""
        patient = self._create_patient()
        enc = Encounter.objects.create(
            patient=patient,
            encounter_type="AMBULATORY",
            reason_for_visit="Checkup",
        )
        user = User.objects.create_user(username="permuser", password="pass")
        perm = Permission.objects.get(codename="view_encounter")
        user.user_permissions.add(perm)
        client = Client()
        client.login(username="permuser", password="pass")
        url = reverse("encounter_detail", kwargs={"pk": enc.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["encounter"].pk == enc.pk

    def test_patient_document_list_pagination(self):
        """Test document list view has pagination."""
        patient = self._create_patient()
        user = User.objects.create_user(username="permuser", password="pass")
        perm = Permission.objects.get(codename="medical_records_view_document")
        user.user_permissions.add(perm)
        client = Client()
        client.login(username="permuser", password="pass")
        url = reverse("patient_document_list", kwargs={"patient_pk": patient.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["paginator"] is not None

    def test_patient_documents_relation(self):
        """Test patient can have multiple documents."""
        patient = self._create_patient()
        pdf1 = self._create_pdf_file()
        pdf2 = self._create_pdf_file()
        pdf2.name = "test2.pdf"
        PatientDocument.objects.create(
            patient=patient, document_type="LAB_REPORT", title="Doc 1", file=pdf1
        )
        PatientDocument.objects.create(
            patient=patient, document_type="XRAY", title="Doc 2", file=pdf2
        )
        assert patient.documents.count() == 2
