def user_roles(request):
    """Adds user role flags and unread notification count to all templates."""
    if not request.user.is_authenticated:
        return {}

    is_admin = (
        request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
    )
    is_doctor = request.user.groups.filter(name="Doctor").exists()
    is_nurse = request.user.groups.filter(name="Nurse").exists()
    is_receptionist = request.user.groups.filter(name="Receptionist").exists()
    is_pharmacist = request.user.groups.filter(name="Pharmacist").exists()
    is_lab_tech = request.user.groups.filter(name="Lab Technician").exists()

    is_surgeon = request.user.groups.filter(name="Surgeon").exists()
    is_anesthesiologist = request.user.groups.filter(name="Anesthesiologist").exists()
    is_radiologist = request.user.groups.filter(name="Radiologist").exists()
    is_technician = request.user.groups.filter(name="Technician").exists()
    is_security = request.user.groups.filter(name="Security").exists()
    is_maintenance = request.user.groups.filter(name="Maintenance").exists()
    is_viewer = request.user.groups.filter(name="Demo Viewer").exists()

    staff_profile = getattr(request.user, "staff_profile", None)
    if staff_profile:
        if staff_profile.role == "DOCTOR":
            is_doctor = True
        elif staff_profile.role == "NURSE":
            is_nurse = True
        elif staff_profile.role == "ADMIN":
            is_admin = True
        elif staff_profile.role == "RECEPTIONIST":
            is_receptionist = True
        elif staff_profile.role == "PHARMACIST":
            is_pharmacist = True
        elif staff_profile.role == "LAB_TECH":
            is_lab_tech = True
        elif staff_profile.role == "SURGEON":
            is_surgeon = True
        elif staff_profile.role == "ANESTHESIOLOGIST":
            is_anesthesiologist = True
        elif staff_profile.role == "RADIOLOGIST":
            is_radiologist = True
        elif staff_profile.role == "TECH":
            is_technician = True
        elif staff_profile.role == "SECURITY":
            is_security = True
        elif staff_profile.role == "MAINTENANCE":
            is_maintenance = True
        elif staff_profile.role == "VIEWER":
            is_viewer = True

    from notifications.models import Notification

    unread_notifications = Notification.objects.filter(status="PENDING").count()

    return {
        "is_hms_admin": is_admin,
        "is_hms_doctor": is_doctor,
        "is_hms_nurse": is_nurse,
        "is_hms_receptionist": is_receptionist,
        "is_hms_pharmacist": is_pharmacist,
        "is_hms_lab_tech": is_lab_tech,
        "is_hms_surgeon": is_surgeon,
        "is_hms_anesthesiologist": is_anesthesiologist,
        "is_hms_radiologist": is_radiologist,
        "is_hms_technician": is_technician,
        "is_hms_security": is_security,
        "is_hms_maintenance": is_maintenance,
        "is_hms_viewer": is_viewer,
        "unread_notifications": unread_notifications,
    }
