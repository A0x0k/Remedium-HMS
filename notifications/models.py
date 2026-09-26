from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.models import RemediumBaseModel


class Notification(RemediumBaseModel):
    TYPES = [
        ("SMS", "SMS"),
        ("EMAIL", "Email"),
        ("WHATSAPP", "WhatsApp"),
    ]

    STATUSES = [
        ("PENDING", "Pending"),
        ("SENT", "Sent"),
        ("FAILED", "Failed"),
        ("RETRYING", "Retrying"),
    ]

    class Meta:
        app_label = "notifications"
        permissions = [
            ("notifications_view_notification", "Can view notification"),
            ("notifications_add_notification", "Can add notification"),
            ("notifications_change_notification", "Can change notification"),
            ("notifications_delete_notification", "Can delete notification"),
        ]
        ordering = ["-sent_at"]

    # Recipient information
    recipient = models.CharField(
        max_length=255, help_text="Phone number or email address"
    )
    notification_type = models.CharField(max_length=10, choices=TYPES)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="PENDING")

    # Link to the entity this notification is about (Patient, Appointment, etc.)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Optional direct FK to patient for quick lookups
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )

    retry_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.notification_type} to {self.recipient} ({self.status})"

    def mark_sent(self):
        """Mark notification as sent."""
        self.status = "SENT"
        self.save(update_fields=["status"])

    def mark_failed(self, error=None):
        """Mark notification as failed with optional error message."""
        self.status = "FAILED"
        if error:
            self.error_message = error
        self.save(update_fields=["status", "error_message"])
