from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField, EncryptedEmailField
from core.models import RemediumBaseModel
from simple_history.models import HistoricalRecords


class Patient(RemediumBaseModel):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("P", "Prefer not to say"),
    ]

    class Meta:
        app_label = "patients"
        permissions = [
            ("patients_view_patient", "Can view patient"),
            ("patients_add_patient", "Can add patient"),
            ("patients_change_patient", "Can change patient"),
            ("patients_delete_patient", "Can delete patient"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(discharge_date__isnull=True)
                | models.Q(discharge_date__gte=models.F("admission_date")),
                name="discharge_after_admission",
            ),
        ]

    # Simplified phone regex: accepts optional + followed by 9-15 digits
    # Supports any country code, not just US (+1)
    phone_regex = RegexValidator(
        regex=r"^\+?\d{9,15}$",
        message="Phone number must be 9-15 digits, optionally with a leading +.",
    )

    unique_id = models.CharField(
        max_length=20, unique=True, help_text="Unique patient identifier"
    )
    first_name = models.CharField(
        max_length=50, db_index=True, help_text="Patient's first name"
    )
    last_name = models.CharField(
        max_length=50, db_index=True, help_text="Patient's last name"
    )
    date_of_birth = models.DateField(db_index=True, help_text="Patient's date of birth")
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        db_index=True,
        help_text="Patient's gender",
    )
    address = EncryptedTextField(blank=True, null=True, help_text="Patient's address")
    phone = EncryptedCharField(
        validators=[phone_regex],
        max_length=20,
        blank=True,
        null=True,
        help_text="Patient's phone number",
    )
    email = EncryptedEmailField(
        blank=True, null=True, help_text="Patient's email address"
    )
    insurance_provider = EncryptedCharField(
        max_length=100, blank=True, null=True, help_text="Insurance provider name"
    )
    emergency_contact_name = models.CharField(
        max_length=100, blank=True, null=True, help_text="Emergency contact name"
    )
    emergency_contact_phone = EncryptedCharField(
        validators=[phone_regex],
        max_length=20,
        blank=True,
        null=True,
        help_text="Emergency contact phone number",
    )
    medical_history = EncryptedTextField(
        blank=True, null=True, help_text="Patient's medical history"
    )
    admission_date = models.DateTimeField(
        blank=True, null=True, help_text="Hospital admission date and time"
    )
    discharge_date = models.DateTimeField(
        blank=True, null=True, help_text="Hospital discharge date and time"
    )
    ward = models.ForeignKey(
        "hospital.Ward",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Assigned ward",
    )
    room = models.ForeignKey(
        "hospital.Room",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Assigned room",
    )

    history = HistoricalRecords()

    def clean(self):
        super().clean()

        # Validate date of birth is not in the future
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError(
                {"date_of_birth": "Date of birth cannot be in the future."}
            )

        # Validate admission and discharge dates
        if self.admission_date and self.discharge_date:
            if self.discharge_date < self.admission_date:
                raise ValidationError(
                    {
                        "discharge_date": "Discharge date cannot be before admission date."
                    }
                )

    def save(self, *args, **kwargs):
        # Allow gender to be provided as display values like "Male" as well as codes like "M"
        if self.gender:
            gender_map = {
                "Male": "M",
                "Female": "F",
                "Other": "O",
                "Prefer not to say": "P",
            }
            self.gender = gender_map.get(self.gender, self.gender)
        super().save(*args, **kwargs)

    @property
    def age(self):
        """Calculate patient's age based on date of birth."""
        if self.date_of_birth:
            today = date.today()
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None

    @property
    def full_name(self):
        """Return patient's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admitted(self):
        """Check if patient is currently admitted."""
        return self.admission_date is not None and self.discharge_date is None

    def __str__(self):
        return f"{self.unique_id} - {self.first_name} {self.last_name}"
