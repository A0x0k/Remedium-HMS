"""
Shared role-based access control mappings.

Kept in one place so the seeding commands and the permission layer cannot
drift apart.
"""

# Maps a Staff role code (staff.models.Staff.ROLE_CHOICES) to the permission
# Group created by the create_groups management command.
#
# Group membership is what makes user.has_perm(...) resolve. The UI
# navigation (core.context_processors) and the API permission classes
# (core.permissions) additionally fall back to staff_profile.role, so a
# seeded account is still navigable if its Group is missing.
ROLE_GROUPS = {
    "ADMIN": "Admin",
    "DOCTOR": "Doctor",
    "NURSE": "Nurse",
    "RECEPTIONIST": "Receptionist",
    "PHARMACIST": "Pharmacist",
    "LAB_TECH": "Lab Technician",
    "SURGEON": "Surgeon",
    "ANESTHESIOLOGIST": "Anesthesiologist",
    "RADIOLOGIST": "Radiologist",
    "TECH": "Technician",
    "SECURITY": "Security",
    "MAINTENANCE": "Maintenance",
    "OTHER": "Other",
    # Read-only demo role. The group carries only *_view_* permissions, so
    # PermissionRequiredMixin lets list/detail pages render while every
    # add/change/delete view raises 403.
    "VIEWER": "Demo Viewer",
}
