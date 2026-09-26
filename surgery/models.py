from django.db import models
from core.models import RemediumBaseModel
from simple_history.models import HistoricalRecords


class Surgery(RemediumBaseModel):
    class Meta:
        app_label = "surgery"
        permissions = [
            ("surgery_view_surgery", "Can view surgery"),
            ("surgery_add_surgery", "Can add surgery"),
            ("surgery_change_surgery", "Can change surgery"),
            ("surgery_delete_surgery", "Can delete surgery"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["operating_room", "scheduled_date"],
                name="unique_operating_room_schedule",
            )
        ]

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    surgeon = models.ForeignKey("staff.Staff", on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    operating_room = models.CharField(max_length=50)
    procedure = models.CharField(max_length=100)
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Scheduled",
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Surgery for {self.patient} by {self.surgeon} on {self.scheduled_date}"

    history = HistoricalRecords()
