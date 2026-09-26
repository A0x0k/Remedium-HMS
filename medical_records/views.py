from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import SuccessQueryParamMixin, DeleteSuccessMixin
from .models import PatientDocument, Encounter
from patients.models import Patient


class EncounterCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Encounter
    fields = [
        "patient",
        "doctor",
        "encounter_type",
        "reason_for_visit",
        "clinical_notes",
        "appointment",
    ]
    template_name = "medical_records/encounter_form.html"
    permission_required = "medical_records.medical_records_add_encounter"
    raise_exception = True
    success_message = "Encounter created successfully."

    def get_initial(self):
        initial = super().get_initial()
        patient_pk = self.request.GET.get("patient")
        appointment_pk = self.request.GET.get("appointment")
        if patient_pk:
            initial["patient"] = get_object_or_404(Patient, pk=patient_pk)
        if appointment_pk:
            from appointments.models import Appointment

            appointment = get_object_or_404(Appointment, pk=appointment_pk)
            initial["appointment"] = appointment
            if not patient_pk:
                initial["patient"] = appointment.patient
            initial["doctor"] = appointment.doctor
            initial["reason_for_visit"] = appointment.reason
        return initial

    def get_success_url(self):
        url = reverse("patient_detail", kwargs={"pk": self.object.patient.pk})
        return f"{url}?created=1"


class PatientDocumentListView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.ListView
):
    model = PatientDocument
    template_name = "medical_records/patient_document_list.html"
    context_object_name = "documents"
    paginate_by = 10
    permission_required = "medical_records.medical_records_view_document"
    raise_exception = True

    def get_queryset(self):
        self.patient = get_object_or_404(Patient, pk=self.kwargs["patient_pk"])
        return PatientDocument.objects.filter(patient=self.patient)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = self.patient
        return context


class EncounterDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Encounter
    template_name = "medical_records/encounter_detail.html"
    context_object_name = "encounter"
    permission_required = "medical_records.view_encounter"
    raise_exception = True


class EncounterUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Encounter
    fields = [
        "patient",
        "doctor",
        "encounter_type",
        "reason_for_visit",
        "clinical_notes",
        "appointment",
        "start_time",
        "end_time",
    ]
    template_name = "medical_records/encounter_form.html"
    permission_required = "medical_records.change_encounter"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Encounter updated successfully."

    def get_success_url(self):
        url = reverse("patient_detail", kwargs={"pk": self.object.patient.pk})
        return f"{url}?updated=1"


class EncounterDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Encounter
    template_name = "medical_records/encounter_confirm_delete.html"
    success_url = reverse_lazy("home")
    permission_required = "medical_records.delete_encounter"
    raise_exception = True
    success_message = "Encounter deleted successfully."


class PatientDocumentCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = PatientDocument
    fields = ["document_type", "title", "file", "notes"]
    template_name = "medical_records/patient_document_form.html"
    permission_required = "medical_records.medical_records_add_document"
    raise_exception = True
    success_message = "Document uploaded successfully."

    def form_valid(self, form):
        form.instance.patient = get_object_or_404(Patient, pk=self.kwargs["patient_pk"])
        return super().form_valid(form)

    def get_success_url(self):
        url = reverse(
            "patient_document_list", kwargs={"patient_pk": self.kwargs["patient_pk"]}
        )
        return f"{url}?created=1"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = get_object_or_404(Patient, pk=self.kwargs["patient_pk"])
        return context
