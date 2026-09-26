"""Tests for inventory app REST API."""

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.test import Client
from rest_framework.test import APIClient
from rest_framework import status
from inventory.models import InventoryItem


def make_admin():
    return User.objects.create_superuser(
        username="inv_admin", password="pass", email="i@i.com"
    )


@pytest.fixture
def admin_client():
    client = APIClient()
    client.force_authenticate(user=make_admin())
    return client


def make_item(**kwargs):
    defaults = {
        "name": "Gloves",
        "category": "PPE",
        "quantity": 100,
        "unit": "BOX",
        "reorder_level": 10,
    }
    defaults.update(kwargs)
    return InventoryItem.objects.create(**defaults)


@pytest.mark.django_db
class TestInventoryAPI:
    def test_list_items(self, admin_client):
        make_item()
        r = admin_client.get("/api/v1/inventory/")
        assert r.status_code == status.HTTP_200_OK
        assert r.data["count"] == 1

    def test_create_item(self, admin_client):
        r = admin_client.post(
            "/api/v1/inventory/",
            {
                "name": "Syringes",
                "category": "MEDICAL_SUPPLIES",
                "quantity": 500,
                "unit": "PIECE",
                "reorder_level": 50,
            },
        )
        assert r.status_code == status.HTTP_201_CREATED
        assert InventoryItem.objects.filter(name="Syringes").exists()

    def test_low_stock_action(self, admin_client):
        make_item(name="Low Item", quantity=5, reorder_level=10)
        make_item(name="OK Item", quantity=100, reorder_level=10)
        r = admin_client.get("/api/v1/inventory/low_stock/")
        assert r.status_code == status.HTTP_200_OK
        names = [i["name"] for i in r.data]
        assert "Low Item" in names
        assert "OK Item" not in names

    def test_serializer_computed_fields(self, admin_client):
        make_item(name="Bandages", quantity=5, reorder_level=10, cost_per_unit="2.50")
        r = admin_client.get("/api/v1/inventory/")
        item = r.data["results"][0]
        assert item["needs_reorder"] is True
        assert item["total_value"] == "12.50"

    def test_unauthenticated_denied(self):
        r = APIClient().get("/api/v1/inventory/")
        assert r.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestInventoryViews:
    """Template rendering tests for InventoryItem views."""

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
        url = reverse("inventoryitem_list")
        response = client.get(url)
        assert response.status_code == 403

    def test_list_with_permission(self):
        client = self._login_with_permission("permuser", "inventory_view_inventoryitem")
        url = reverse("inventoryitem_list")
        response = client.get(url)
        assert response.status_code == 200
        assert "inventory_items" in response.context

    def test_detail_requires_permission(self):
        item = InventoryItem.objects.create(
            name="Gloves", category="PPE", quantity=100, unit="BOX"
        )
        User.objects.create_user(username="testuser", password="pass")
        client = Client()
        client.login(username="testuser", password="pass")
        url = reverse("inventoryitem_detail", kwargs={"pk": item.pk})
        response = client.get(url)
        assert response.status_code == 403

    def test_detail_with_permission(self):
        item = InventoryItem.objects.create(
            name="Gloves", category="PPE", quantity=100, unit="BOX"
        )
        client = self._login_with_permission("permuser", "inventory_view_inventoryitem")
        url = reverse("inventoryitem_detail", kwargs={"pk": item.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["item"].pk == item.pk
