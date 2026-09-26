from django.db import models
from core.models import RemediumBaseModel
from simple_history.models import HistoricalRecords


class Prescription(RemediumBaseModel):
    class Meta:
        app_label = "pharmacy"
        permissions = [
            ("pharmacy_view_prescription", "Can view prescription"),
            ("pharmacy_add_prescription", "Can add prescription"),
            ("pharmacy_change_prescription", "Can change prescription"),
            ("pharmacy_delete_prescription", "Can delete prescription"),
        ]

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    service = models.ForeignKey(
        "hospital.HospitalService",
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"category": "PHARMACY"},
    )
    drug_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specific medication name (overrides service name if provided)",
    )
    dosage = models.CharField(max_length=50)
    frequency = models.CharField(max_length=50)
    prescribed_date = models.DateTimeField(auto_now_add=True)
    prescribed_by = models.ForeignKey(
        "staff.Staff", on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("Active", "Active"),
            ("Completed", "Completed"),
            ("Discontinued", "Discontinued"),
        ],
        default="Active",
    )
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.drug_name} for {self.patient}"

    history = HistoricalRecords()
