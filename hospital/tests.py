"""Tests for hospital app REST API."""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.test import Client
from rest_framework.test import APIClient
from rest_framework import status
from hospital.models import Ward, Room, HospitalService


def make_admin():
    return User.objects.create_superuser(
        username="hosp_admin", password="pass", email="h@h.com"
    )


@pytest.fixture
def admin_client():
    client = APIClient()
    client.force_authenticate(user=make_admin())
    return client


@pytest.mark.django_db
class TestWardAPI:
    def test_list_wards(self, admin_client):
        Ward.objects.create(name="ICU", capacity=10)
        r = admin_client.get("/api/v1/wards/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["count"] == 1

    def test_create_ward(self, admin_client):
        r = admin_client.post("/api/v1/wards/", {"name": "Pediatrics", "capacity": 20})
        assert r.status_code == status.HTTP_201_CREATED
        assert Ward.objects.filter(name="Pediatrics").exists()

    def test_update_ward(self, admin_client):
        ward = Ward.objects.create(name="Old", capacity=5)
        r = admin_client.patch(f"/api/v1/wards/{ward.pk}/", {"capacity": 15})
        assert r.status_code == status.HTTP_200_OK
        ward.refresh_from_db()
        assert ward.capacity == 15

    def test_delete_ward(self, admin_client):
        ward = Ward.objects.create(name="Temp", capacity=3)
        r = admin_client.delete(f"/api/v1/wards/{ward.pk}/")
        assert r.status_code == status.HTTP_204_NO_CONTENT

    def test_unauthenticated_denied(self):
        r = APIClient().get("/api/v1/wards/")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestRoomAPI:
    def test_list_rooms(self, admin_client):
        ward = Ward.objects.create(name="General", capacity=10)
        Room.objects.create(ward=ward, room_number="101", capacity=2)
        r = admin_client.get("/api/v1/rooms/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["count"] == 1

    def test_create_room(self, admin_client):
        ward = Ward.objects.create(name="Surgical", capacity=8)
        r = admin_client.post(
            "/api/v1/rooms/", {"ward": ward.pk, "room_number": "201", "capacity": 2}
        )
        assert r.status_code == status.HTTP_201_CREATED

    def test_room_serializer_includes_ward_name(self, admin_client):
        ward = Ward.objects.create(name="Maternity", capacity=6)
        Room.objects.create(ward=ward, room_number="301", capacity=1)
        r = admin_client.get("/api/v1/rooms/")
        assert r.data["results"][0]["ward_name"] == "Maternity"


@pytest.mark.django_db
class TestWardViews:
    """Template rendering tests for Ward/Room views."""

    def _login_with_permission(self, username, codename):
        client = Client()
        user = User.objects.create_user(username=username, password="pass")
        perm = Permission.objects.get(codename=codename, content_type__app_label="hospital")
        user.user_permissions.add(perm)
        client.login(username=username, password="pass")
        return client

    def test_ward_list_requires_permission(self):
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("hospital:ward_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_ward_list_with_permission(self):
        client = self._login_with_permission("permuser", "view_ward")
        url = reverse("hospital:ward_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "wards" in response.context

    def test_ward_detail_with_permission(self):
        ward = Ward.objects.create(name="ICU", capacity=10)
        client = self._login_with_permission("permuser", "view_ward")
        url = reverse("hospital:ward_detail", kwargs={"pk": ward.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["ward"].pk == ward.pk

    def test_service_list_with_permission(self):
        HospitalService.objects.create(
            name="X-Ray", category="LABORATORY", base_price=100.00
        )
        client = self._login_with_permission("permuser", "view_hospitalservice")
        url = reverse("hospital:service_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "services" in response.context

    def test_occupancy_map_with_permission(self):
        client = self._login_with_permission("permuser", "view_ward")
        url = reverse("hospital:occupancy_map")
        response = client.get(url)
        assert response.status_code == 200
        assert "wards" in response.context
