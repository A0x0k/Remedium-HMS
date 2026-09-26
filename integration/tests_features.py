from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, datetime
from patients.models import Patient
from staff.models import Staff, Shift
from appointments.models import Appointment
from medical_records.models import PatientDocument
from billing.models import Invoice, Payment
from notifications.models import Notification
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError


class FeatureIntegrationTest(TestCase):
    def setUp(self):
        # Setup Patient
        self.patient = Patient.objects.create(
            unique_id="PAT_TEST_001",
            first_name="Test",
            last_name="Patient",
            date_of_birth="1990-01-01",
            gender="M",
            phone="+1234567890",
            email="test@patient.com",
        )

        # Setup Doctor
        self.doctor = Staff.objects.create(
            staff_id="DOC_TEST_001",
            first_name="Test",
            last_name="Doctor",
            role="DOCTOR",
            department="CARDIOLOGY",
            phone="+1987654321",
            email="doctor@hospital.com",
        )

    def test_scheduling_logic(self):
        # 1. Define Shift: Monday (0) 09:00 - 17:00
        Shift.objects.create(
            staff=self.doctor,
            day_of_week=0,  # Monday
            start_time="09:00",
            end_time="17:00",
        )

        # 2. Try to book on Monday at 08:00 (Outside shift)
        # Find next Monday
        today = timezone.now().date()
        days_ahead = 0 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = today + timedelta(days=days_ahead)

        appt_time_invalid = timezone.make_aware(
            datetime.combine(next_monday, datetime.strptime("08:00", "%H:%M").time())
        )

        appt = Appointment(
            patient=self.patient, doctor=self.doctor, appointment_date=appt_time_invalid
        )

        with self.assertRaises(ValidationError) as cm:
            appt.full_clean()
        self.assertIn("Doctor does not have a shift", str(cm.exception))

        # 3. Book on Monday at 10:00 (Inside shift)
        appt_time_valid = timezone.make_aware(
            datetime.combine(next_monday, datetime.strptime("10:00", "%H:%M").time())
        )
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, appointment_date=appt_time_valid
        )
        # Should succeed without error

    def test_ehr_versioning(self):
        # Update patient details
        self.patient.address = "New Address 123"
        self.patient.save()

        # Check history
        self.assertTrue(self.patient.history.count() > 0)
        latest_history = self.patient.history.first()
        self.assertEqual(latest_history.address, "New Address 123")

        # Update again
        self.patient.address = "Another Address 456"
        self.patient.save()
        self.assertEqual(self.patient.history.count(), 3)  # Initial create + 2 updates

    def test_document_upload(self):
        doc_file = SimpleUploadedFile(
            "test_report.pdf", b"file_content", content_type="application/pdf"
        )
        doc = PatientDocument.objects.create(
            patient=self.patient,
            document_type="LAB_REPORT",
            title="Blood Test",
            file=doc_file,
        )
        self.assertEqual(doc.title, "Blood Test")
        self.assertTrue(doc.file.name.startswith("patient_documents/"))

    def test_payment_processing(self):
        invoice = Invoice.objects.create(
            patient=self.patient,
            total_amount=100.00,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),
        )

        # Partial Payment
        Payment.objects.create(invoice=invoice, amount=50.00, payment_method="CASH")
        invoice.refresh_from_db()
        self.assertFalse(invoice.paid)

        # Remaining Payment
        Payment.objects.create(invoice=invoice, amount=50.00, payment_method="CARD")
        invoice.refresh_from_db()
        self.assertTrue(invoice.paid)

    def test_notification_signal(self):
        # Create appointment to trigger signal
        # Use a time that works (assume no shift check for this test or doctor has no shifts so check is skipped?)
        # Wait, my logic in clean(): "if self.doctor.shifts.exists() and not has_shift".
        # If doctor has NO shifts, the check is skipped.

        # Clear shifts for this test logic simplicity or add a shift
        # The doctor here is self.doctor, which has NO shifts created in setUp.
        # So clean() should pass.

        appt_time = timezone.now() + timedelta(days=1)
        Appointment.objects.create(
            patient=self.patient, doctor=self.doctor, appointment_date=appt_time
        )

        # Check notifications
        notifications = Notification.objects.filter(recipient=self.patient.email)
        self.assertTrue(notifications.exists())
        self.assertEqual(notifications.first().notification_type, "EMAIL")
        self.assertIn("scheduled for", notifications.first().message)
