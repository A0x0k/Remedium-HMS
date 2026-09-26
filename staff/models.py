from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from core.models import RemediumBaseModel
from simple_history.models import HistoricalRecords

# Shared phone validator - same as Patient model
phone_regex = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="Phone number must be 9-15 digits, optionally with a leading +.",
)


class Staff(RemediumBaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_profile",
        help_text="System user account associated with this staff member",
    )
    ROLE_CHOICES = [
        ("DOCTOR", "Doctor"),
        ("NURSE", "Nurse"),
        ("ADMIN", "Administrator"),
        ("TECH", "Technician"),
        ("PHARMACIST", "Pharmacist"),
        ("RECEPTIONIST", "Receptionist"),
        ("SURGEON", "Surgeon"),
        ("ANESTHESIOLOGIST", "Anesthesiologist"),
        ("RADIOLOGIST", "Radiologist"),
        ("LAB_TECH", "Laboratory Technician"),
        ("SECURITY", "Security"),
        ("MAINTENANCE", "Maintenance"),
        ("OTHER", "Other"),
        # Read-only role used by the public demo account. It is deliberately
        # absent from every ALLOWED_ROLES/MEDICAL_ROLES list in
        # core.permissions, so role-gated API endpoints reject it outright.
        ("VIEWER", "Read-only Viewer"),
    ]

    DEPARTMENT_CHOICES = [
        ("EMERGENCY", "Emergency Department"),
        ("CARDIOLOGY", "Cardiology"),
        ("NEUROLOGY", "Neurology"),
        ("ORTHOPEDICS", "Orthopedics"),
        ("PEDIATRICS", "Pediatrics"),
        ("SURGERY", "Surgery"),
        ("ICU", "Intensive Care Unit"),
        ("ONCOLOGY", "Oncology"),
        ("RADIOLOGY", "Radiology"),
        ("LABORATORY", "Laboratory"),
        ("PHARMACY", "Pharmacy"),
        ("ADMINISTRATION", "Administration"),
        ("MAINTENANCE", "Maintenance"),
        ("SECURITY", "Security"),
        ("OTHER", "Other"),
    ]

    class Meta:
        app_label = "staff"
        permissions = [
            ("staff_view_staff", "Can view staff"),
            ("staff_add_staff", "Can add staff"),
            ("staff_change_staff", "Can change staff"),
            ("staff_delete_staff", "Can delete staff"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(email__isnull=False),
                name="unique_staff_email",
            ),
        ]

    # Uses shared phone_validator defined at module level

    staff_id = models.CharField(
        max_length=20, unique=True, help_text="Unique staff identifier"
    )
    first_name = models.CharField(max_length=50, help_text="Staff member's first name")
    last_name = models.CharField(max_length=50, help_text="Staff member's last name")
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, help_text="Staff member's role/position"
    )
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True,
        help_text="Department where staff member works",
    )
    phone = models.CharField(
        validators=[phone_regex], max_length=20, help_text="Staff member's phone number"
    )
    email = models.EmailField(
        blank=True, null=True, help_text="Staff member's email address"
    )
    schedule = models.TextField(
        blank=True, null=True, help_text="Staff member's work schedule"
    )
    hire_date = models.DateField(
        auto_now_add=True, help_text="Date when staff member was hired"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether the staff member is currently active"
    )

    history = HistoricalRecords()

    def clean(self):
        super().clean()

        # Validate role-department compatibility
        role_department_map = {
            "PHARMACIST": "PHARMACY",
            "LAB_TECH": "LABORATORY",
            "RADIOLOGIST": "RADIOLOGY",
            "SURGEON": "SURGERY",
            "ANESTHESIOLOGIST": "SURGERY",
        }

        if self.role in role_department_map and self.department:
            if self.department != role_department_map[self.role]:
                raise ValidationError(
                    {
                        "department": f"{self.get_role_display()} should be in {role_department_map[self.role]} department."
                    }
                )

    def save(self, *args, **kwargs):
        """Normalize data and run full validation before saving."""
        # Allow using human-readable role labels like "Doctor" in addition to codes like "DOCTOR"
        if self.role:
            role_map = {
                "Doctor": "DOCTOR",
                "Nurse": "NURSE",
                "Administrator": "ADMIN",
                "Technician": "TECH",
                "Pharmacist": "PHARMACIST",
                "Receptionist": "RECEPTIONIST",
                "Surgeon": "SURGEON",
                "Anesthesiologist": "ANESTHESIOLOGIST",
                "Radiologist": "RADIOLOGIST",
                "Laboratory Technician": "LAB_TECH",
                "Security": "SECURITY",
                "Maintenance": "MAINTENANCE",
                "Other": "OTHER",
            }
            self.role = role_map.get(self.role, self.role)

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Return staff member's full name."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_medical_staff(self):
        """Check if staff member is medical personnel."""
        medical_roles = [
            "DOCTOR",
            "NURSE",
            "SURGEON",
            "ANESTHESIOLOGIST",
            "RADIOLOGIST",
        ]
        return self.role in medical_roles

    def __str__(self):
        return f"{self.staff_id} - {self.first_name} {self.last_name} ({self.role})"


class Shift(RemediumBaseModel):
    DAYS_OF_WEEK = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="shifts")
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week", "start_time"]
        unique_together = ["staff", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.staff} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"
