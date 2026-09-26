from django.views import generic
from .models import Patient
from .forms import PatientForm
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin


class PatientListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Patient
    template_name = "patients/patient_list.html"
    context_object_name = "patients"
    paginate_by = 10
    permission_required = "patients.patients_view_patient"
    raise_exception = True

    ALLOWED_ORDER_BY = [
        "last_name",
        "first_name",
        "admission_date",
        "unique_id",
        "-last_name",
        "-first_name",
        "-admission_date",
        "-unique_id",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q")
        order_by = self.request.GET.get("order_by", "last_name")
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "last_name"
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(unique_id__icontains=query)
            )
        return queryset.select_related("ward", "room").order_by(order_by)


class PatientDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Patient
    template_name = "patients/patient_detail.html"
    context_object_name = "patient"
    permission_required = "patients.patients_view_patient"
    raise_exception = True

    def get_queryset(self):
        return Patient.objects.select_related("ward", "room").all()

    def get_context_data(self, **kwargs):
        import json

        context = super().get_context_data(**kwargs)
        p = self.object
        context["breadcrumbs"] = [
            {"label": "Patients", "url": "/patients/"},
            {"label": p.full_name},
        ]
        context["appointments"] = p.appointment_set.select_related("doctor").order_by(
            "-appointment_date"
        )[:10]
        care_records = list(p.patientcare_set.order_by("monitoring_date")[:20])
        context["care_records"] = care_records
        context["prescriptions"] = p.prescription_set.select_related(
            "prescribed_by"
        ).order_by("-prescribed_date")[:10]
        context["lab_tests"] = p.labtest_set.order_by("-requested_date")[:10]
        context["encounters"] = p.encounters.select_related("doctor").order_by(
            "-start_time"
        )[:10]
        context["documents"] = p.documents.all()[:10]
        context["chart_data"] = json.dumps(
            {
                "dates": [
                    r.monitoring_date.strftime("%b %d %H:%M") for r in care_records
                ],
                "heart_rates": [r.heart_rate or None for r in care_records],
                "temperatures": [
                    float(r.temperature) if r.temperature else None
                    for r in care_records
                ],
                "systolic": [r.blood_pressure_systolic or None for r in care_records],
                "diastolic": [r.blood_pressure_diastolic or None for r in care_records],
                "oxygen": [
                    float(r.oxygen_saturation) if r.oxygen_saturation else None
                    for r in care_records
                ],
            }
        )
        return context


class PatientCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    success_url = reverse_lazy("patient_list")
    permission_required = "patients.patients_add_patient"
    raise_exception = True
    success_message = "Patient created successfully."


class PatientUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Patient
    form_class = PatientForm
    template_name = "patients/patient_form.html"
    success_url = reverse_lazy("patient_list")
    permission_required = "patients.patients_change_patient"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Patient updated successfully."


class PatientDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Patient
    template_name = "patients/patient_confirm_delete.html"
    success_url = reverse_lazy("patient_list")
    permission_required = "patients.patients_delete_patient"
    raise_exception = True
    success_message = "Patient deleted successfully."


class PatientHistoryView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Patient
    template_name = "patients/patient_history.html"
    context_object_name = "patient"
    permission_required = "patients.patients_view_patient"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        raw_history = self.object.history.all()
        context["history"] = [
            {
                "entry": record,
                "changes": (
                    record.diff_against(record.prev_record).changes
                    if record.prev_record
                    else None
                ),
            }
            for record in raw_history
        ]
        return context
