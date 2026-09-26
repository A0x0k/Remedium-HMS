from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.contrib.auth.decorators import (
    login_required,
    permission_required as perm_decorator,
)
from django.utils import timezone
from .models import Appointment
from .forms import AppointmentForm


class AppointmentListView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.ListView
):
    model = Appointment
    template_name = "appointments/appointment_list.html"
    context_object_name = "appointments"
    paginate_by = 10
    permission_required = "appointments.appointments_view_appointment"
    raise_exception = True

    ALLOWED_ORDER_BY = ["appointment_date", "status", "-appointment_date", "-status"]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("patient", "doctor")
        order_by = self.request.GET.get("order_by", "appointment_date")
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "appointment_date"
        return queryset.order_by(order_by)


class AppointmentCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Appointment
    form_class = AppointmentForm
    template_name = "appointments/appointment_form.html"
    success_url = reverse_lazy("appointment_list")
    permission_required = "appointments.appointments_add_appointment"
    raise_exception = True
    success_message = "Appointment created successfully."


class AppointmentUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Appointment
    form_class = AppointmentForm
    template_name = "appointments/appointment_form.html"
    success_url = reverse_lazy("appointment_list")
    permission_required = "appointments.appointments_change_appointment"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Appointment updated successfully."


class AppointmentDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Appointment
    template_name = "appointments/appointment_confirm_delete.html"
    success_url = reverse_lazy("appointment_list")
    permission_required = "appointments.appointments_delete_appointment"
    raise_exception = True
    success_message = "Appointment deleted successfully."


class AppointmentDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView
):
    model = Appointment
    context_object_name = "appointment"
    permission_required = "appointments.appointments_view_appointment"
    raise_exception = True


@login_required
@perm_decorator("appointments.appointments_change_appointment")
def check_in_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    appointment.status = "Waiting"
    appointment.arrived_at = timezone.now()
    appointment.save()
    return redirect("appointment_list")


class QueueTrackerView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Appointment
    template_name = "appointments/queue_tracker.html"
    context_object_name = "queue"
    paginate_by = 10
    permission_required = "appointments.appointments_view_appointment"
    raise_exception = True

    def get_queryset(self):
        return (
            Appointment.objects.filter(status__in=["Waiting", "In Progress"])
            .select_related("patient", "doctor")
            .order_by("appointment_date")
        )
