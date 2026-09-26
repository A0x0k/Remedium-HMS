from django.views import generic
from .forms import LabTestForm
from .models import LabTest
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin


class LabTestListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = LabTest
    template_name = "laboratory/labtest_list.html"
    context_object_name = "lab_tests"
    paginate_by = 10  # Add pagination
    permission_required = "laboratory.laboratory_view_labtest"
    raise_exception = True

    ALLOWED_ORDER_BY = ["requested_date", "status", "-requested_date", "-status"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "service")
        order_by = self.request.GET.get("order_by", "requested_date")
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "requested_date"
        return queryset.order_by(order_by)


class LabTestDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = LabTest
    template_name = "laboratory/labtest_detail.html"
    context_object_name = "lab_test"
    permission_required = "laboratory.laboratory_view_labtest"
    raise_exception = True


class LabTestCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = LabTest
    form_class = LabTestForm
    template_name = "laboratory/labtest_form.html"
    success_url = reverse_lazy("labtest_list")
    permission_required = "laboratory.laboratory_add_labtest"
    raise_exception = True
    success_message = "Lab test created successfully."


class LabTestUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = LabTest
    form_class = LabTestForm
    template_name = "laboratory/labtest_form.html"
    success_url = reverse_lazy("labtest_list")
    permission_required = "laboratory.laboratory_change_labtest"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Lab test updated successfully."


class LabTestDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = LabTest
    template_name = "laboratory/labtest_confirm_delete.html"
    success_url = reverse_lazy("labtest_list")
    permission_required = "laboratory.laboratory_delete_labtest"
    raise_exception = True
    success_message = "Lab test deleted successfully."


# Create your views here.
