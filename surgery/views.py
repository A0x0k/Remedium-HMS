from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.views import generic
from .forms import SurgeryForm
from .models import Surgery


class SurgeryListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Surgery
    template_name = "surgery/surgery_list.html"
    context_object_name = "surgeries"
    paginate_by = 10  # Add pagination
    permission_required = "surgery.surgery_view_surgery"
    raise_exception = True

    ALLOWED_ORDER_BY = ["scheduled_date", "status", "-scheduled_date", "-status"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "surgeon")
        order_by = self.request.GET.get("order_by", "scheduled_date")
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "scheduled_date"
        return queryset.order_by(order_by)


class SurgeryDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Surgery
    template_name = "surgery/surgery_detail.html"
    context_object_name = "surgery"
    permission_required = "surgery.surgery_view_surgery"
    raise_exception = True

    def get_queryset(self):
        return Surgery.objects.select_related("patient", "surgeon").all()


class SurgeryCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Surgery
    form_class = SurgeryForm
    template_name = "surgery/surgery_form.html"
    success_url = reverse_lazy("surgery_list")
    permission_required = "surgery.surgery_add_surgery"
    raise_exception = True
    success_message = "Surgery scheduled successfully."


class SurgeryUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Surgery
    form_class = SurgeryForm
    template_name = "surgery/surgery_form.html"
    success_url = reverse_lazy("surgery_list")
    permission_required = "surgery.surgery_change_surgery"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Surgery updated successfully."


class SurgeryDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Surgery
    template_name = "surgery/surgery_confirm_delete.html"
    success_url = reverse_lazy("surgery_list")
    permission_required = "surgery.surgery_delete_surgery"
    raise_exception = True
    success_message = "Surgery cancelled successfully."


# Create your views here.
