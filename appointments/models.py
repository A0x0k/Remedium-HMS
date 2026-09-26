from django.db import models
from patients.models import Patient
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import RemediumBaseModel
from simple_history.models import HistoricalRecords


class Appointment(RemediumBaseModel):
    class Meta:
        app_label = "appointments"
        permissions = [
            ("appointments_view_appointment", "Can view appointment"),
            ("appointments_add_appointment", "Can add appointment"),
            ("appointments_change_appointment", "Can change appointment"),
            ("appointments_delete_appointment", "Can delete appointment"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "doctor", "appointment_date"],
                name="unique_appointment",
            )
        ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey("staff.Staff", on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    reason = models.TextField(blank=True, null=True)
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Waiting", "Waiting/Arrived"),
        ("In Progress", "In Progress"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Scheduled", db_index=True
    )
    arrived_at = models.DateTimeField(
        blank=True, null=True, help_text="Time when patient arrived at clinic"
    )

    history = HistoricalRecords()

    def clean(self):
        super().clean()
        if self.appointment_date and self.appointment_date < timezone.now():
            raise ValidationError(
                {"appointment_date": "Appointment date cannot be in the past."}
            )

        # Check for conflicts with existing appointments using proper range overlap
        # Two ranges overlap when: start_a < end_b AND start_b < end_a
        duration = timezone.timedelta(minutes=30)  # Assuming 30 min slots
        new_start = self.appointment_date
        new_end = self.appointment_date + duration

        # Check for overlapping appointments: existing appointment that starts before new_end AND ends after new_start
        # Since we don't store end time, we assume all appointments are 30 minutes
        overlapping = Appointment.objects.filter(
            doctor=self.doctor,
            appointment_date__lt=new_end,  # existing start < new end
            appointment_date__gte=new_start
            - duration,  # existing start >= (new start - duration)
            status="Scheduled",
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError(
                {
                    "appointment_date": "This time slot is already booked for this doctor."
                }
            )

        # Check against Doctor's Shift
        # Note: This is a strict check. In real world, might need overrides.
        day_of_week = self.appointment_date.weekday()
        time = self.appointment_date.time()

        has_shift = self.doctor.shifts.filter(
            day_of_week=day_of_week,
            start_time__lte=time,
            end_time__gte=time,  # Simplified: logic usually needs to check if slot fits strictly within
        ).exists()

        # If the doctor has NO shifts defined, we might assume they are available or unavailable.
        # Here we assume if they have shifts, we must respect them.
        if self.doctor.shifts.exists() and not has_shift:
            raise ValidationError(
                {"appointment_date": "Doctor does not have a shift at this time."}
            )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appointment_date}"
