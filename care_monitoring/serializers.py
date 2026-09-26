from rest_framework import serializers
from .models import PatientCare


class PatientCareSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    blood_pressure = serializers.CharField(read_only=True)
    bmi = serializers.FloatField(read_only=True)
    is_vital_signs_critical = serializers.BooleanField(read_only=True)

    class Meta:
        model = PatientCare
        fields = [
            "id",
            "patient",
            "patient_name",
            "status",
            "monitoring_date",
            "temperature",
            "heart_rate",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "blood_pressure",
            "respiratory_rate",
            "oxygen_saturation",
            "weight",
            "height",
            "bmi",
            "notes",
            "monitored_by",
            "is_vital_signs_critical",
        ]
        read_only_fields = ["id", "monitoring_date"]

    def validate(self, data):
        systolic = data.get("blood_pressure_systolic")
        diastolic = data.get("blood_pressure_diastolic")
        if systolic and diastolic and systolic <= diastolic:
            raise serializers.ValidationError(
                {
                    "blood_pressure_systolic": "Systolic pressure must be higher than diastolic pressure."
                }
            )
        return data
