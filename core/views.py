from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, F
from django.db import connections
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from appointments.models import Appointment
from patients.models import Patient
from billing.models import Invoice
from staff.models import Staff
from care_monitoring.models import PatientCare
from pharmacy.models import Prescription
from laboratory.models import LabTest
from surgery.models import Surgery
from inventory.models import InventoryItem


# ---------------------------------------------------------------------------
# Role helpers
# ---------------------------------------------------------------------------

def get_role(request):
    """Determine user role from staff profile, falling back to superuser check."""
    staff_profile = getattr(request.user, "staff_profile", None)
    if staff_profile:
        return staff_profile.role
    if request.user.is_superuser:
        return "ADMIN"
    return "OTHER"


def get_role_template(role):
    """Map role code to the appropriate dashboard template."""
    mapping = {
        "ADMIN": "dashboards/admin_dashboard.html",
        "DOCTOR": "dashboards/doctor_dashboard.html",
        "NURSE": "dashboards/nurse_dashboard.html",
        "RECEPTIONIST": "dashboards/receptionist_dashboard.html",
        "PHARMACIST": "dashboards/pharmacist_dashboard.html",
        "LAB_TECH": "dashboards/labtech_dashboard.html",
        "SURGEON": "dashboards/surgeon_dashboard.html",
        "ANESTHESIOLOGIST": "dashboards/surgeon_dashboard.html",
    }
    return mapping.get(role, "dashboards/default_dashboard.html")


def get_role_display(role):
    """Return a human-readable label for a role code."""
    mapping = {
        "ADMIN": "Administrator",
        "DOCTOR": "Physician",
        "NURSE": "Nursing Staff",
        "RECEPTIONIST": "Receptionist",
        "PHARMACIST": "Pharmacist",
        "LAB_TECH": "Lab Technician",
        "SURGEON": "Surgeon",
        "ANESTHESIOLOGIST": "Anesthesiologist",
        "RADIOLOGIST": "Radiologist",
        "TECH": "Technician",
        "SECURITY": "Security",
        "MAINTENANCE": "Maintenance",
        "OTHER": "Staff",
    }
    return mapping.get(role, "Staff")


# ---------------------------------------------------------------------------
# Per-role context builders
# ---------------------------------------------------------------------------

def _common_context(today):
    """Context shared across all authenticated roles."""
    return {
        "total_patients": Patient.objects.count(),
        "admitted_patients": Patient.objects.filter(
            admission_date__isnull=False, discharge_date__isnull=True
        ).count(),
        "recent_patients": Patient.objects.select_related("ward", "room").order_by(
            "-admission_date"
        )[:5],
        "now": timezone.now(),
        "today_appointments": Appointment.objects.filter(
            appointment_date__date=today, status="Scheduled"
        ).count(),
        "upcoming_appointments": (
            Appointment.objects.filter(
                appointment_date__gte=timezone.now(), status="Scheduled"
            )
            .select_related("patient", "doctor")
            .order_by("appointment_date")[:5]
        ),
    }


def _admin_context(today):
    """Extra context for Admin / superuser dashboards."""
    day_name_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    revenue_by_day = []
    day_labels = []
    appt_by_day = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_revenue = (
            Invoice.objects.filter(paid=True, issue_date=day).aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0
        )
        revenue_by_day.append(float(day_revenue))
        day_labels.append(day_name_map[day.weekday()])
        appt_by_day.append(Appointment.objects.filter(appointment_date__date=day).count())

    dept_stats = list(
        Staff.objects.values("department")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    if dept_stats:
        max_count = dept_stats[0]["count"]
        for d in dept_stats:
            d["pct"] = int(d["count"] / max_count * 100) if max_count else 0

    return {
        "unpaid_invoices": Invoice.objects.filter(paid=False).count(),
        "paid_invoices": Invoice.objects.filter(paid=True).count(),
        "total_revenue": Invoice.objects.filter(paid=True).aggregate(
            total=Sum("total_amount")
        )["total"] or 0,
        "active_staff": Staff.objects.filter(is_active=True).count(),
        "discharged_patients": Patient.objects.filter(
            discharge_date__isnull=False
        ).count(),
        "completed_today": Appointment.objects.filter(
            appointment_date__date=today, status="Completed"
        ).count(),
        "on_duty_today": Staff.objects.filter(is_active=True).count(),
        "recent_invoices": Invoice.objects.select_related("patient").order_by(
            "-issue_date"
        )[:5],
        "dept_stats": dept_stats,
        "chart_revenue_data": revenue_by_day,
        "chart_day_labels": day_labels,
        "chart_appointments_data": appt_by_day,
    }


def _doctor_context(staff_profile, today):
    """Extra context for Doctor dashboards."""
    return {
        "my_appointments": (
            Appointment.objects.filter(
                doctor=staff_profile,
                appointment_date__date=today,
                status="Scheduled",
            )
            .select_related("patient")
            .order_by("appointment_date")[:5]
        ),
        "my_pending_appointments": Appointment.objects.filter(
            doctor=staff_profile,
            appointment_date__date=today,
            status="Scheduled",
        ).count(),
        "my_patient_count": Appointment.objects.filter(doctor=staff_profile)
        .values("patient")
        .distinct()
        .count(),
        "active_care_count": PatientCare.objects.filter(
            status__in=["STABLE", "CRITICAL"]
        ).count(),
        "my_prescriptions_count": Prescription.objects.filter(
            prescribed_by=staff_profile
        ).count(),
        "recent_vitals": PatientCare.objects.select_related("patient").order_by(
            "-monitoring_date"
        )[:5],
        "upcoming_surgeries": Surgery.objects.filter(
            scheduled_date__gte=timezone.now()
        )
        .select_related("patient")
        .order_by("scheduled_date")[:5],
    }


def _nurse_context(today):
    """Extra context for Nurse dashboards."""
    return {
        "active_care_count": PatientCare.objects.filter(
            status__in=["STABLE", "CRITICAL"]
        ).count(),
        "critical_count": PatientCare.objects.filter(status="CRITICAL").count(),
        "stable_count": PatientCare.objects.filter(status="STABLE").count(),
        "recent_vitals": PatientCare.objects.select_related("patient").order_by(
            "-monitoring_date"
        )[:5],
        "critical_care": PatientCare.objects.filter(status="CRITICAL")
        .select_related("patient")
        .order_by("-monitoring_date")[:5],
        "recent_admissions_count": Patient.objects.filter(
            admission_date__gte=today - timedelta(days=7)
        ).count(),
    }


def _receptionist_context(today):
    """Extra context for Receptionist dashboards."""
    return {
        "available_doctors": Staff.objects.filter(
            role="DOCTOR", is_active=True
        ).count(),
        "new_patients_7days": Patient.objects.filter(
            admission_date__gte=today - timedelta(days=7)
        ).count(),
        "checked_in_count": Appointment.objects.filter(
            appointment_date__date=today, status="Scheduled"
        ).count(),
    }


def _pharmacist_context(today):
    """Extra context for Pharmacist dashboards."""
    return {
        "active_prescriptions": Prescription.objects.filter(status="Active").count(),
        "pending_dispense": Prescription.objects.filter(status="Active").count(),
        "new_prescriptions_today": Prescription.objects.filter(
            prescribed_date__date=today
        ).count(),
        "dispensed_today": Prescription.objects.filter(
            prescribed_date__date=today
        ).count(),
        "low_stock_count": InventoryItem.objects.filter(
            quantity__lte=F("reorder_level")
        ).count(),
        "low_stock_items": list(
            InventoryItem.objects.filter(quantity__lte=F("reorder_level"))[:5]
        ),
        "pending_prescriptions": Prescription.objects.filter(status="Active")
        .select_related("patient", "prescribed_by")
        .order_by("-prescribed_date")[:10],
    }


def _labtech_context(today):
    """Extra context for Lab Technician dashboards."""
    return {
        "pending_tests": LabTest.objects.filter(status="Requested").count(),
        "completed_today": LabTest.objects.filter(
            requested_date__date=today, status="Completed"
        ).count(),
        "in_progress_tests": LabTest.objects.filter(status="In Progress").count(),
        "requests_today": LabTest.objects.filter(requested_date__date=today).count(),
        "pending_lab_tests": LabTest.objects.filter(status="Requested")
        .select_related("patient")
        .order_by("-requested_date")[:10],
        "recent_completed": LabTest.objects.filter(status="Completed")
        .select_related("patient")
        .order_by("-requested_date")[:5],
    }


def _surgeon_context(staff_profile, role, today):
    """Extra context for Surgeon / Anesthesiologist dashboards."""
    surgeon_filter = {"surgeon": staff_profile} if role == "SURGEON" else {}
    return {
        "upcoming_surgeries_count": Surgery.objects.filter(
            scheduled_date__gte=timezone.now(), **surgeon_filter
        ).count(),
        "surgeries_today": Surgery.objects.filter(
            scheduled_date__date=today, **surgeon_filter
        ).count(),
        "completed_surgeries_7days": Surgery.objects.filter(
            scheduled_date__gte=today - timedelta(days=7),
            status="Completed",
            **surgeon_filter,
        ).count(),
        "my_patient_count": Surgery.objects.filter(**surgeon_filter)
        .values("patient")
        .distinct()
        .count(),
        "pre_op_count": Surgery.objects.filter(
            status="Scheduled", **surgeon_filter
        ).count(),
        "consult_count": 0,
        "today_surgeries": Surgery.objects.filter(
            scheduled_date__date=today, **surgeon_filter
        )
        .select_related("patient")
        .order_by("scheduled_date")[:5],
        "upcoming_surgeries": Surgery.objects.filter(
            scheduled_date__gte=timezone.now(), **surgeon_filter
        )
        .select_related("patient")
        .order_by("scheduled_date")[:5],
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

def homepage(request):
    if not request.user.is_authenticated:
        return render(request, "landing.html", {})

    staff_profile = getattr(request.user, "staff_profile", None)
    role = get_role(request)
    today = timezone.now().date()

    context = _common_context(today)
    context["role_display"] = get_role_display(role)

    if role == "ADMIN" or request.user.is_superuser:
        context.update(_admin_context(today))

    if role == "DOCTOR" and staff_profile:
        context.update(_doctor_context(staff_profile, today))

    if role == "NURSE":
        context.update(_nurse_context(today))

    if role == "RECEPTIONIST":
        context.update(_receptionist_context(today))

    if role == "PHARMACIST":
        context.update(_pharmacist_context(today))

    if role == "LAB_TECH":
        context.update(_labtech_context(today))

    if role in ("SURGEON", "ANESTHESIOLOGIST") and staff_profile:
        context.update(_surgeon_context(staff_profile, role, today))

    return render(request, get_role_template(role), context)


def logout_view(request):
    logout(request)
    return redirect("login")


def health_check(request):
    health = {"status": "healthy", "database": "connected"}
    status_code = 200
    try:
        conn = connections["default"]
        conn.ensure_connection()
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "unhealthy"
        status_code = 503
    return JsonResponse(health, status=status_code)


@login_required
@user_passes_test(
    lambda u: u.is_superuser
    or (hasattr(u, "staff_profile") and u.staff_profile.role == "ADMIN")
)
def audit_log(request):
    from patients.models import Patient
    from staff.models import Staff
    from appointments.models import Appointment
    from billing.models import Invoice

    all_history = sorted(
        list(Patient.history.all()[:20])
        + list(Staff.history.all()[:20])
        + list(Appointment.history.all()[:20])
        + list(Invoice.history.all()[:20]),
        key=lambda x: x.history_date,
        reverse=True,
    )[:50]
    for entry in all_history:
        try:
            entry.model_name = entry.instance._meta.verbose_name.title()
        except Exception:
            entry.model_name = type(entry).__name__.replace("Historical", "")
    return render(request, "core/audit_logs.html", {"history": all_history})


class DeleteSuccessMixin:
    """Appends ?deleted=1 to the success URL so the list page shows a toast."""

    def get_success_url(self):
        url = super().get_success_url()
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}deleted=1"


class SuccessQueryParamMixin:
    """Appends ?created=1 or ?updated=1 to the success URL."""

    success_query_param = "created"

    def get_success_url(self):
        url = super().get_success_url()
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{self.success_query_param}=1"
