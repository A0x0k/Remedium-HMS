from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from core.views import DeleteSuccessMixin, SuccessQueryParamMixin
from django.contrib.auth.decorators import (
    login_required,
    permission_required as perm_decorator,
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages
from django.views import generic
from .forms import StaffForm, StaffWithUserForm
from .models import Staff, Shift


from django.utils import timezone
from django.db.models import Count, Q
from medical_records.models import Encounter


class DoctorAvailabilityView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.ListView
):
    """
    Dashboard view for receptionists to see current doctor load and availability.
    """

    model = Staff
    template_name = "staff/doctor_availability.html"
    context_object_name = "doctors"
    permission_required = "staff.staff_view_staff"
    raise_exception = True

    def get_queryset(self):
        # Filter for medical staff (Doctors, Surgeons, etc.)
        medical_roles = ["DOCTOR", "SURGEON", "ANESTHESIOLOGIST", "RADIOLOGIST"]
        now = timezone.now()
        current_day = now.weekday()
        current_time = now.time()

        queryset = (
            Staff.objects.filter(role__in=medical_roles, is_active=True)
            .annotate(
                active_cases_count=Count(
                    "encounter_set", filter=Q(encounter_set__end_time__isnull=True)
                )
            )
            .prefetch_related("shifts")
        )

        # Determine if each doctor is currently on shift
        for doctor in queryset:
            doctor.on_shift = doctor.shifts.filter(
                day_of_week=current_day,
                start_time__lte=current_time,
                end_time__gte=current_time,
            ).exists()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class StaffListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Staff
    template_name = "staff/staff_list.html"
    context_object_name = (
        "staff_list"  # Changed to staff_list to avoid conflict with template variable
    )
    paginate_by = 10  # Add pagination
    permission_required = "staff.staff_view_staff"
    raise_exception = True
    ALLOWED_ORDER_BY = [
        "last_name",
        "first_name",
        "staff_id",
        "role",
        "department",
        "-last_name",
        "-first_name",
        "-staff_id",
        "-role",
        "-department",
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        order_by = self.request.GET.get(
            "order_by", "last_name"
        )  # Default sort by last_name
        if order_by not in self.ALLOWED_ORDER_BY:
            order_by = "last_name"
        return queryset.order_by(order_by)


class StaffDetailView(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Staff
    template_name = "staff/staff_detail.html"
    context_object_name = "staff"
    permission_required = "staff.staff_view_staff"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["shifts"] = self.object.shifts.all()
        return context


class StaffCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    model = Staff
    form_class = StaffForm  # Use the custom form class
    template_name = "staff/staff_form.html"
    success_url = reverse_lazy("staff_list")  # Redirect to the list view after success
    permission_required = "staff.staff_add_staff"
    raise_exception = True
    success_message = "Staff member created successfully."


class StaffUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.UpdateView
):
    model = Staff
    form_class = StaffForm  # Use the custom form class
    template_name = "staff/staff_form.html"
    success_url = reverse_lazy("staff_list")  # Redirect to the list view after success
    permission_required = "staff.staff_change_staff"
    raise_exception = True
    success_query_param = "updated"
    success_message = "Staff member updated successfully."


class StaffDeleteView(
    DeleteSuccessMixin, LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Staff
    template_name = "staff/staff_confirm_delete.html"
    success_url = reverse_lazy("staff_list")  # Redirect to the list view after success
    permission_required = "staff.staff_delete_staff"
    raise_exception = True
    success_message = "Staff member deleted successfully."


class ShiftCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.CreateView
):
    model = Shift
    fields = ["day_of_week", "start_time", "end_time"]
    template_name = "staff/shift_form.html"
    permission_required = "staff.staff_change_staff"
    raise_exception = True
    success_message = "Shift created successfully."

    def form_valid(self, form):
        form.instance.staff = get_object_or_404(Staff, pk=self.kwargs["staff_pk"])
        return super().form_valid(form)

    def get_success_url(self):
        url = reverse("staff_detail", kwargs={"pk": self.kwargs["staff_pk"]})
        return f"{url}?created=1"


class ShiftDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessMessageMixin, generic.DeleteView
):
    model = Shift
    template_name = "staff/shift_confirm_delete.html"
    permission_required = "staff.staff_change_staff"
    raise_exception = True
    success_message = "Shift deleted successfully."

    def get_success_url(self):
        url = reverse("staff_detail", kwargs={"pk": self.object.staff.pk})
        return f"{url}?deleted=1"


# User Management Views


class UserListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Staff
    template_name = "staff/user_list.html"
    context_object_name = "users_list"
    permission_required = "auth.view_user"  # Needs appropriate permission
    raise_exception = True

    def get_queryset(self):
        # Only show staff that have a linked user account
        return (
            Staff.objects.filter(user__isnull=False)
            .select_related("user")
            .order_by("user__username")
        )


class UserCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessQueryParamMixin, SuccessMessageMixin,
    generic.CreateView
):
    form_class = StaffWithUserForm
    template_name = "staff/user_form.html"
    success_url = reverse_lazy("user_list")
    permission_required = "auth.add_user"
    raise_exception = True
    success_message = "User account created successfully."


@login_required
@perm_decorator("auth.change_user")
def toggle_user_status(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if staff.user:
        user = staff.user
        user.is_active = not user.is_active
        user.save()

        staff.is_active = user.is_active
        staff.save()

        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f"User {user.username} has been {status}.")

    return redirect("user_list")


@login_required
@perm_decorator("auth.change_user")
def admin_reset_password(request, pk):
    staff = get_object_or_404(Staff, pk=pk)
    if staff.user:
        user = staff.user
        if user.email:
            form = PasswordResetForm({"email": user.email})
            if form.is_valid():
                form.save(request=request, use_https=request.is_secure())
                messages.success(
                    request, f"A password reset email has been sent to {user.email}."
                )
        else:
            user.set_unusable_password()
            user.save(update_fields=["password"])
            messages.warning(
                request,
                f"Password login for {user.username} has been disabled because the account has no email address.",
            )

    return redirect("user_list")
