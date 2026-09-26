from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "appointment_date", "reason"]
        widgets = {
            "appointment_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")

        if doctor and appointment_date:
            if (
                Appointment.objects.filter(
                    doctor=doctor, appointment_date=appointment_date
                )
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise forms.ValidationError(
                    "This doctor is already booked for this time slot."
                )
