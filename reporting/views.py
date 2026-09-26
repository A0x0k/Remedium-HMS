from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.views import generic
from django.urls import reverse_lazy
from patients.models import Patient
from .forms import ReportForm
from .models import Report


class ReportListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Report
    template_name = "reporting/report_list.html"
    context_object_name = "reports"
    paginate_by = 10  # Add pagination
    permission_required = "reporting.reporting_view_report"
    raise_exception = True

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.GET.get(
            "order_by", "created_at"
        )  # Default sort by created_at
        return queryset.order_by(order_by)


class ReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Report
    template_name = "reporting/report_detail.html"
    context_object_name = "report"
    permission_required = "reporting.reporting_view_report"
    raise_exception = True


class ReportCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Report
    form_class = ReportForm
    template_name = "reporting/report_form.html"
    success_url = reverse_lazy("report_list")
    permission_required = "reporting.reporting_add_report"
    raise_exception = True
    success_message = "Report created successfully."


class ReportUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Report
    form_class = ReportForm
    template_name = "reporting/report_form.html"
    success_url = reverse_lazy("report_list")
    permission_required = "reporting.reporting_change_report"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Report updated successfully."


class ReportDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Report
    template_name = "reporting/report_confirm_delete.html"
    success_url = reverse_lazy("report_list")
    permission_required = "reporting.reporting_delete_report"
    raise_exception = True
    success_message = "Report deleted successfully."


@login_required
@permission_required("reporting.view_report")
def patient_report(request):
    num_patients = Patient.objects.count()
    report_html = f"<h1>Patient Report</h1><p>Number of patients: {num_patients}</p>"
    return HttpResponse(report_html)


@login_required
@permission_required("reporting.view_report")
def download_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    response = HttpResponse(report.data, content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{report.title}.txt"'
    return response
