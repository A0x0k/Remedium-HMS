"""Tests for staff app."""

import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.test import Client
from staff.models import Staff


@pytest.mark.django_db
class TestStaffModel:
    """Test Staff model."""

    def test_create_staff(self):
        """Test basic staff creation."""
        staff = Staff.objects.create(
            staff_id="STF001",
            first_name="John",
            last_name="Doe",
            role="Doctor",
        )
        assert staff.pk is not None
        assert str(staff) == "STF001 - John Doe (DOCTOR)"

    def test_full_name_property(self):
        """Test full_name property."""
        staff = Staff(
            staff_id="STF002",
            first_name="Jane",
            last_name="Smith",
            role="Nurse",
        )
        assert staff.full_name == "Jane Smith"

    def test_staff_id_must_be_unique(self):
        """Test staff_id constraint."""
        Staff.objects.create(
            staff_id="DUP_STF",
            first_name="First",
            last_name="User",
            role="Admin",
        )
        with pytest.raises(Exception):  # IntegrityError
            Staff.objects.create(
                staff_id="DUP_STF",
                first_name="Second",
                last_name="User",
                role="Admin",
            )


@pytest.mark.django_db
class TestStaffViews:
    """Template rendering tests for Staff views."""

    def _create_staff(self):
        return Staff.objects.create(
            staff_id="STF_VW",
            first_name="Test",
            last_name="Staff",
            role="DOCTOR",
        )

    def _login_with_permission(self, username, codename):
        client = Client()
        user = User.objects.create_user(username=username, password="pass")
        perm = Permission.objects.get(codename=codename)
        user.user_permissions.add(perm)
        client.login(username=username, password="pass")
        return client

    def test_list_requires_permission(self):
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("staff_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_list_with_permission(self):
        client = self._login_with_permission("permuser", "staff_view_staff")
        url = reverse("staff_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "staff_list" in response.context

    def test_detail_requires_permission(self):
        staff = self._create_staff()
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("staff_detail", kwargs={"pk": staff.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_detail_with_permission(self):
        staff = self._create_staff()
        client = self._login_with_permission("permuser", "staff_view_staff")
        url = reverse("staff_detail", kwargs={"pk": staff.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["staff"].pk == staff.pk

    def test_create_requires_permission(self):
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("staff_create")
        response = client.get(url)
        assert response.status_code == 403

    def test_create_with_permission(self):
        client = self._login_with_permission("permuser", "staff_add_staff")
        url = reverse("staff_create")
        response = client.get(url)
        assert response.status_code == 200

    def test_doctor_availability_with_permission(self):
        self._create_staff()
        client = self._login_with_permission("permuser", "staff_view_staff")
        url = reverse("doctor_availability")
        response = client.get(url)
        assert response.status_code == 200
