from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.views import generic
from django.urls import reverse_lazy
from .models import PatientCare


class PatientCareForm(forms.ModelForm):
    """Form for PatientCare that excludes auto-managed fields."""

    class Meta:
        model = PatientCare
        fields = [
            "patient",
            "status",
            "temperature",
            "heart_rate",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "respiratory_rate",
            "oxygen_saturation",
            "weight",
            "height",
            "notes",
            "monitored_by",
        ]


class PatientCareListView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.ListView
):
    model = PatientCare
    template_name = "care_monitoring/patientcare_list.html"
    context_object_name = "patientcares"
    paginate_by = 10
    permission_required = "care_monitoring.care_monitoring_view_patientcare"
    raise_exception = True

    ALLOWED_ORDER_BY = ["monitoring_date", "status", "-monitoring_date", "-status"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "monitored_by")
        order_by = self.request.GET.get("order_by", "monitoring_date")
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "monitoring_date"
        return queryset.order_by(order_by)


class PatientCareDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = PatientCare
    template_name = "care_monitoring/patientcare_detail.html"
    context_object_name = "patientcare"
    permission_required = "care_monitoring.care_monitoring_view_patientcare"
    raise_exception = True

    def get_queryset(self):
        return PatientCare.objects.select_related("patient", "monitored_by").all()


class PatientCareCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = PatientCare
    form_class = PatientCareForm
    template_name = "care_monitoring/patientcare_form.html"
    success_url = reverse_lazy("care_monitoring:patientcare_list")
    permission_required = "care_monitoring.care_monitoring_add_patientcare"
    raise_exception = True
    success_message = "Care record created successfully."


class PatientCareUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = PatientCare
    form_class = PatientCareForm
    template_name = "care_monitoring/patientcare_form.html"
    success_url = reverse_lazy("care_monitoring:patientcare_list")
    permission_required = "care_monitoring.care_monitoring_change_patientcare"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Care record updated successfully."


class PatientCareDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = PatientCare
    template_name = "care_monitoring/patientcare_confirm_delete.html"
    success_url = reverse_lazy("care_monitoring:patientcare_list")
    permission_required = "care_monitoring.care_monitoring_delete_patientcare"
    raise_exception = True
    success_message = "Care record deleted successfully."


class PatientVitalTrendsView(LoginRequiredMixin, PermissionRequiredMixin, generic.View):
    """Redirect to patient detail — vitals chart is embedded in the Vitals tab."""

    permission_required = "care_monitoring.care_monitoring_view_patientcare"
    raise_exception = True

    def get(self, request, pk):
        from django.shortcuts import redirect

        return redirect("patient_detail", pk=pk)
