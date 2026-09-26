from django.db import models
from core.models import RemediumBaseModel
from simple_history.models import HistoricalRecords


class LabTest(RemediumBaseModel):
    class Meta:
        app_label = "laboratory"
        permissions = [
            ("laboratory_view_labtest", "Can view lab test"),
            ("laboratory_add_labtest", "Can add lab test"),
            ("laboratory_change_labtest", "Can change lab test"),
            ("laboratory_delete_labtest", "Can delete lab test"),
        ]

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    service = models.ForeignKey(
        "hospital.HospitalService",
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"category": "LABORATORY"},
    )
    test_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specific test name (overrides service name if provided)",
    )
    requested_date = models.DateTimeField(auto_now_add=True)
    result_date = models.DateTimeField(blank=True, null=True)
    result = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("Requested", "Requested"),
            ("Completed", "Completed"),
            ("Cancelled", "Cancelled"),
        ],
        default="Requested",
    )

    def __str__(self):
        return f"{self.test_name} for {self.patient}"

    history = HistoricalRecords()
