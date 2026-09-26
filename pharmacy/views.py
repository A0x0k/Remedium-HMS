from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.views import generic
from .forms import PrescriptionForm
from .models import Prescription


class PrescriptionListView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.ListView
):
    model = Prescription
    template_name = "pharmacy/prescription_list.html"
    context_object_name = "prescriptions"
    paginate_by = 10  # Add pagination
    permission_required = "pharmacy.pharmacy_view_prescription"
    raise_exception = True

    def get_queryset(self):
        queryset = (
            super().get_queryset().select_related("patient", "service", "prescribed_by")
        )
        order_by = self.request.GET.get(
            "order_by", "prescribed_date"
        )  # Default sort by prescribed_date
        return queryset.order_by(order_by)


class PrescriptionDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Prescription
    template_name = "pharmacy/prescription_detail.html"
    context_object_name = "prescription"
    permission_required = "pharmacy.pharmacy_view_prescription"
    raise_exception = True


class PrescriptionCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "pharmacy/prescription_form.html"
    success_url = reverse_lazy("prescription_list")
    permission_required = "pharmacy.pharmacy_add_prescription"
    raise_exception = True
    success_message = "Prescription created successfully."


class PrescriptionUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Prescription
    form_class = PrescriptionForm
    template_name = "pharmacy/prescription_form.html"
    success_url = reverse_lazy("prescription_list")
    permission_required = "pharmacy.pharmacy_change_prescription"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Prescription updated successfully."


class PrescriptionDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Prescription
    template_name = "pharmacy/prescription_confirm_delete.html"
    success_url = reverse_lazy("prescription_list")
    permission_required = "pharmacy.pharmacy_delete_prescription"
    raise_exception = True
    success_message = "Prescription deleted successfully."


# Create your views here.
