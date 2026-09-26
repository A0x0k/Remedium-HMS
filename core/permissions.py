"""
Custom permission classes for role-based API access control.

Usage:
    permission_classes = [IsAdminOrDoctor]
    permission_classes = [IsClinicalStaff]
    permission_classes = [IsAdminUser]
"""

from rest_framework import permissions
from staff.models import Staff


class IsAdminUser(permissions.BasePermission):
    """Only Django staff users or HMS administrators can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.staff_profile.role == "ADMIN"
        except (AttributeError, Staff.DoesNotExist):
            return False


class IsAdminOrDoctor(permissions.BasePermission):
    """Admin users or doctors can access."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.staff_profile.role in ["DOCTOR", "SURGEON"]
        except (AttributeError, Staff.DoesNotExist):
            return False


class IsClinicalStaff(permissions.BasePermission):
    """Any clinical staff (doctor, nurse, surgeon, etc.) can access."""

    MEDICAL_ROLES = [
        "DOCTOR",
        "NURSE",
        "SURGEON",
        "ANESTHESIOLOGIST",
        "RADIOLOGIST",
        "PHARMACIST",
        "LAB_TECH",
    ]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.staff_profile.role in self.MEDICAL_ROLES
        except (AttributeError, Staff.DoesNotExist):
            return False


class IsBillingStaff(permissions.BasePermission):
    """Admin, receptionists, and billing-related staff can access invoices."""

    ALLOWED_ROLES = ["ADMIN", "RECEPTIONIST", "BILLING"]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.staff_profile.role in self.ALLOWED_ROLES
        except (AttributeError, Staff.DoesNotExist):
            return False


class IsLabStaff(permissions.BasePermission):
    """Admin, lab techs, radiologists, doctors, and nurses can access lab tests."""

    ALLOWED_ROLES = ["ADMIN", "LAB_TECH", "RADIOLOGIST", "DOCTOR", "NURSE"]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.staff_profile.role in self.ALLOWED_ROLES
        except (AttributeError, Staff.DoesNotExist):
            return False


class IsPharmacyStaff(permissions.BasePermission):
    """Admin, pharmacists, doctors, and nurses can access prescriptions."""

    ALLOWED_ROLES = ["ADMIN", "PHARMACIST", "DOCTOR", "NURSE"]

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        try:
            return request.user.staff_profile.role in self.ALLOWED_ROLES
        except (AttributeError, Staff.DoesNotExist):
            return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission: only staff with appropriate permissions can edit, anyone authenticated can view."""

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for staff with appropriate permissions
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        # Check if user has permission to change this type of object.
        # Custom permissions in this project are declared as
        # "<app_label>_<action>_<model>" (e.g. patients_change_patient),
        # so the lookup codename must carry the app_label prefix too.
        # Plain "change_<model>" matches only Django's auto-generated
        # defaults, which no group is ever granted.
        if hasattr(obj, "_meta"):
            app_label = obj._meta.app_label
            model_name = obj._meta.model_name
            return request.user.has_perm(f"{app_label}.{app_label}_change_{model_name}")
        return False
