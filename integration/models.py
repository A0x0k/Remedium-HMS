from django.db import models
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from cryptography.fernet import Fernet
from core.models import RemediumBaseModel


def get_encryption_key():
    """Return the dedicated Fernet key used for database-stored secrets."""
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
    if not key:
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY must be set before storing integration API keys."
        )
    return key.encode()


def encrypt_value(value):
    """Encrypt a value using Fernet symmetric encryption."""
    if not value:
        return value
    f = Fernet(get_encryption_key())
    return f.encrypt(value.encode()).decode()


def decrypt_value(value):
    """Decrypt a Fernet-encrypted value."""
    if not value:
        return value
    f = Fernet(get_encryption_key())
    return f.decrypt(value.encode()).decode()


class ExternalIntegration(RemediumBaseModel):
    SYSTEM_TYPES = [
        ("EMR", "Electronic Medical Records"),
        ("PHARMACY_HUB", "External Pharmacy Hub"),
        ("INSURANCE", "Insurance Gateway"),
        ("LAB_EQUIPMENT", "Laboratory Equipment"),
    ]

    system_name = models.CharField(max_length=100)
    system_type = models.CharField(max_length=20, choices=SYSTEM_TYPES, default="EMR")
    api_endpoint = models.URLField()
    api_key = models.CharField(
        max_length=512,
        blank=True,
        null=True,
        help_text="Encrypted API Key (use set_api_key/get_api_key methods)",
    )

    def set_api_key(self, raw_key):
        """Encrypt and store the API key."""
        self.api_key = encrypt_value(raw_key)

    def get_api_key(self):
        """Decrypt and return the API key."""
        if not self.api_key:
            return None
        return decrypt_value(self.api_key)

    last_sync = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=50, default="Inactive")
    last_sync_result = models.JSONField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def trigger_sync(self):
        """Trigger synchronization with the external system.

        Not yet implemented. Wire up a real HTTP call or a Celery task here.
        """
        raise NotImplementedError(
            f"trigger_sync() is not implemented for {self.system_name}. "
            "Integrate a real HTTP call or a Celery task before calling this method."
        )

    def __str__(self):
        return f"{self.system_name} ({self.get_system_type_display()})"


# Create your models here.
