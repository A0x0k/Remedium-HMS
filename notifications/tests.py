"""Tests for notifications app."""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.test import Client
from notifications.models import Notification
from patients.models import Patient


@pytest.mark.django_db
class TestNotificationModel:
    """Test Notification model."""

    def _create_patient(self):
        return Patient.objects.create(
            unique_id="PAT_NOTIF",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )

    def test_create_notification(self):
        patient = self._create_patient()
        notif = Notification.objects.create(
            recipient="+1234567890",
            notification_type="SMS",
            message="Your appointment is tomorrow at 10 AM",
            patient=patient,
        )
        assert notif.pk is not None
        assert notif.status == "PENDING"
        assert "SMS" in str(notif)

    def test_notification_status_choices(self):
        """Test valid status values."""
        for status in ["PENDING", "SENT", "FAILED", "RETRYING"]:
            notif = Notification(
                recipient="test@example.com",
                notification_type="EMAIL",
                message="Test message",
                status=status,
            )
            notif.full_clean()  # Should not raise

    def test_mark_sent(self):
        """Test mark_sent method."""
        notif = Notification.objects.create(
            recipient="+1234567890",
            notification_type="SMS",
            message="Test",
        )
        assert notif.status == "PENDING"
        notif.mark_sent()
        notif.refresh_from_db()
        assert notif.status == "SENT"

    def test_mark_failed(self):
        """Test mark_failed method with error message."""
        notif = Notification.objects.create(
            recipient="bad@number",
            notification_type="SMS",
            message="Test",
        )
        notif.mark_failed("Invalid phone number")
        notif.refresh_from_db()
        assert notif.status == "FAILED"
        assert notif.error_message == "Invalid phone number"

    def test_patient_relation(self):
        """Test notifications can be accessed from patient."""
        patient = Patient.objects.create(
            unique_id="PAT_NOTIF2",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )
        Notification.objects.create(
            recipient="+1111111111",
            notification_type="SMS",
            message="Notification 1",
            patient=patient,
        )
        Notification.objects.create(
            recipient="+2222222222",
            notification_type="SMS",
            message="Notification 2",
            patient=patient,
        )
        assert patient.notifications.count() == 2

    def _login_with_permission(self, username, codename):
        client = Client()
        user = User.objects.create_user(username=username, password="pass")
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
        client.login(username=username, password="pass")
        return client

    def test_notification_list_view_requires_permission(self):
        """Test that notification list requires view_notification permission."""
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("notification_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_notification_list_view_with_permission(self):
        """Test notification list loads with proper permission."""
        client = self._login_with_permission("permuser", "view_notification")
        url = reverse("notification_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "notifications" in response.context

    def test_mark_read_requires_post(self):
        """Test mark_read only accepts POST."""
        client = self._login_with_permission("testuser2", "change_notification")
        notif = Notification.objects.create(
            recipient="test@test.com",
            notification_type="EMAIL",
            message="Test",
        )
        url = reverse("notification_mark_read", kwargs={"pk": notif.pk})
        response = client.get(url)
        assert response.status_code == 405

    def test_mark_read_success(self):
        """Test mark_read updates status to SENT."""
        client = self._login_with_permission("testuser3", "change_notification")
        notif = Notification.objects.create(
            recipient="test@test.com",
            notification_type="EMAIL",
            message="Test",
        )
        url = reverse("notification_mark_read", kwargs={"pk": notif.pk})
        response = client.post(url)
        assert response.status_code == 302
        notif.refresh_from_db()
        assert notif.status == "SENT"

    def test_mark_all_read_success(self):
        """Test mark_all_read updates all pending notifications."""
        client = self._login_with_permission("testuser4", "change_notification")
        Notification.objects.create(
            recipient="test@test.com",
            notification_type="EMAIL",
            message="Pending 1",
            status="PENDING",
        )
        Notification.objects.create(
            recipient="test@test.com",
            notification_type="EMAIL",
            message="Pending 2",
            status="PENDING",
        )
        url = reverse("notification_mark_all_read")
        response = client.post(url)
        assert response.status_code == 302
        assert Notification.objects.filter(status="PENDING").count() == 0
        assert Notification.objects.filter(status="SENT").count() == 2

    def test_notification_ordering(self):
        """Test notifications are ordered by sent_at descending."""
        patient = Patient.objects.create(
            unique_id="PAT_NOTIF3",
            first_name="Test",
            last_name="Patient",
            date_of_birth=timezone.now().date() - timedelta(days=365 * 30),
            gender="M",
        )
        Notification.objects.create(
            recipient="user1@test.com",
            notification_type="EMAIL",
            message="First",
            patient=patient,
        )
        n2 = Notification.objects.create(
            recipient="user2@test.com",
            notification_type="EMAIL",
            message="Second",
            patient=patient,
        )
        # Latest should be first
        all_notifs = list(Notification.objects.filter(patient=patient))
        assert all_notifs[0].pk == n2.pk
