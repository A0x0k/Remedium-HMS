from django.db import models
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
from core.models import RemediumBaseModel


class PatientCare(RemediumBaseModel):
    STATUS_CHOICES = [
        ("STABLE", "Stable"),
        ("CRITICAL", "Critical"),
        ("IMPROVING", "Improving"),
        ("DETERIORATING", "Deteriorating"),
        ("DISCHARGED", "Discharged"),
        ("OBSERVATION", "Under Observation"),
    ]

    class Meta:
        app_label = "care_monitoring"
        permissions = [
            ("care_monitoring_view_patientcare", "Can view patient care"),
            ("care_monitoring_add_patientcare", "Can add patient care"),
            ("care_monitoring_change_patientcare", "Can change patient care"),
            ("care_monitoring_delete_patientcare", "Can delete patient care"),
        ]
        ordering = ["-monitoring_date"]

    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        help_text="Patient being monitored",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, help_text="Patient's current status"
    )
    monitoring_date = models.DateTimeField(
        auto_now_add=True, help_text="Date and time of monitoring"
    )

    # Vital Signs
    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal("35.0")),
            MaxValueValidator(Decimal("45.0")),
        ],
        help_text="Body temperature in Celsius",
    )
    heart_rate = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(30), MaxValueValidator(200)],
        help_text="Heart rate (beats per minute)",
    )
    blood_pressure_systolic = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(60), MaxValueValidator(250)],
        help_text="Systolic blood pressure (mmHg)",
    )
    blood_pressure_diastolic = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(30), MaxValueValidator(150)],
        help_text="Diastolic blood pressure (mmHg)",
    )
    respiratory_rate = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(8), MaxValueValidator(50)],
        help_text="Respiratory rate (breaths per minute)",
    )
    oxygen_saturation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Oxygen saturation percentage",
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal("0.1")),
            MaxValueValidator(Decimal("500.0")),
        ],
        help_text="Weight in kilograms",
    )
    height = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal("0.1")),
            MaxValueValidator(Decimal("250.0")),
        ],
        help_text="Height in centimeters",
    )

    notes = models.TextField(
        blank=True, null=True, help_text="Additional notes and observations"
    )

    monitored_by = models.ForeignKey(
        "staff.Staff",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Staff member who recorded the monitoring",
    )

    history = HistoricalRecords()

    def clean(self):
        super().clean()

        # Validate blood pressure readings
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            if self.blood_pressure_systolic <= self.blood_pressure_diastolic:
                raise ValidationError(
                    {
                        "blood_pressure_systolic": "Systolic pressure must be higher than diastolic pressure."
                    }
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def blood_pressure(self):
        """Return formatted blood pressure reading."""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None

    @property
    def bmi(self):
        """Calculate BMI if height and weight are available."""
        if self.weight and self.height:
            height_m = float(self.height) / 100  # Convert cm to meters
            return round(float(self.weight) / (height_m**2), 2)
        return None

    @property
    def is_vital_signs_critical(self):
        """Check if any vital signs indicate critical condition."""
        critical_conditions = [
            self.temperature and (self.temperature < 36.0 or self.temperature > 40.0),
            self.heart_rate and (self.heart_rate < 50 or self.heart_rate > 120),
            self.blood_pressure_systolic
            and (
                self.blood_pressure_systolic < 90 or self.blood_pressure_systolic > 180
            ),
            self.oxygen_saturation and self.oxygen_saturation < 95.0,
            self.respiratory_rate
            and (self.respiratory_rate < 12 or self.respiratory_rate > 25),
        ]
        return any(critical_conditions)

    def __str__(self):
        return f"Care for {self.patient} on {self.monitoring_date}"
