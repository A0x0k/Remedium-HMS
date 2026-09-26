"""
Regression tests for authorization and template URL integrity.

These cover bugs that produced runtime 500s or silently denied access:

- ``IsOwnerOrReadOnly`` built a ``has_perm`` lookup using Django's default
  ``change_<model>`` codename, but every custom permission in this project is
  declared as ``<app_label>_<action>_<model>``. The lookup never matched, so
  object-level writes were denied for every non-``is_staff`` user.
- Two templates reversed ``medical_records:encounter_create`` even though
  ``medical_records.urls`` is included without a namespace, raising
  ``NoReverseMatch`` and 500-ing the doctor dashboard and the doctor
  availability page.
"""

import re
from pathlib import Path

import pytest
from django.contrib.auth.models import Group, Permission, User
from django.core.management import call_command
from django.urls import get_resolver, reverse

from core.permissions import IsOwnerOrReadOnly
from patients.models import Patient

PROJECT_ROOT = Path(__file__).resolve().parent.parent

URL_TAG_PATTERN = re.compile(r"\{%\s*url\s+(?:'([^']+)'|\"([^\"]+)\")")


def _template_dirs():
    dirs = [PROJECT_ROOT / "templates"]
    for entry in PROJECT_ROOT.iterdir():
        if entry.is_dir() and entry.name != "venv" and (entry / "templates").is_dir():
            dirs.append(entry / "templates")
    return dirs


def _resolvable_url_names():
    """Every URL name the root resolver can reverse, namespaced included."""
    resolver = get_resolver()
    names = {k for k in resolver.reverse_dict.keys() if isinstance(k, str)}
    for namespace, entry in resolver.namespace_dict.items():
        urlconf = entry[1] if isinstance(entry, tuple) else entry
        for key in getattr(urlconf, "reverse_dict", {}).keys():
            if isinstance(key, str):
                names.add(f"{namespace}:{key}")
    return names


class TestIsOwnerOrReadOnly:
    """The has_perm lookup must use this project's custom codename format."""

    @pytest.fixture
    def patient(self, db):
        return Patient.objects.create(
            first_name="Perm",
            last_name="Test",
            date_of_birth="1990-01-01",
            gender="M",
        )

    def _request(self, user, method):
        class _Req:
            pass

        req = _Req()
        req.user = user
        req.method = method
        return req

    def test_read_allowed_for_any_authenticated_user(self, patient):
        from django.contrib.auth.models import User

        user = User.objects.create_user("readonly", password="x")
        assert IsOwnerOrReadOnly().has_object_permission(
            self._request(user, "GET"), None, patient
        ) is True

    def test_write_denied_without_change_permission(self, patient):
        from django.contrib.auth.models import User

        user = User.objects.create_user("noperm", password="x")
        assert IsOwnerOrReadOnly().has_object_permission(
            self._request(user, "POST"), None, patient
        ) is False

    def test_write_allowed_with_custom_codename_permission(self, patient):
        """A user granted patients_change_patient must be able to write.

        Django's auto-generated change_patient permission is deliberately not
        used: create_groups grants the app-prefixed custom codename.
        """
        from django.contrib.auth.models import User

        user = User.objects.create_user("withperm", password="x")
        user.user_permissions.add(
            Permission.objects.get(codename="patients_change_patient")
        )
        user = User.objects.get(pk=user.pk)  # drop the perm cache

        assert IsOwnerOrReadOnly().has_object_permission(
            self._request(user, "POST"), None, patient
        ) is True

    def test_group_permission_also_grants_write(self, patient):
        """Permission inherited from a Group must resolve too."""
        from django.contrib.auth.models import User

        group = Group.objects.create(name="TempPatientEditors")
        group.permissions.add(
            Permission.objects.get(codename="patients_change_patient")
        )
        user = User.objects.create_user("groupuser", password="x")
        user.groups.add(group)
        user = User.objects.get(pk=user.pk)

        assert IsOwnerOrReadOnly().has_object_permission(
            self._request(user, "POST"), None, patient
        ) is True
        group.delete()

    def test_default_django_codename_is_not_silently_accepted(self, patient):
        """Guard the regression: change_patient alone must not grant access."""
        from django.contrib.auth.models import User

        user = User.objects.create_user("defpermonly", password="x")
        user.user_permissions.add(
            Permission.objects.get(codename="change_patient")
        )
        user = User.objects.get(pk=user.pk)

        assert IsOwnerOrReadOnly().has_object_permission(
            self._request(user, "POST"), None, patient
        ) is False


class TestTemplateUrlsResolve:
    """Every {% url %} tag in every template must reverse successfully."""

    def test_no_unresolvable_url_tags(self):
        known = _resolvable_url_names()
        broken = {}

        for template_dir in _template_dirs():
            if not template_dir.exists():
                continue
            for template in template_dir.rglob("*.html"):
                text = template.read_text(encoding="utf-8", errors="ignore")
                for match in URL_TAG_PATTERN.finditer(text):
                    name = match.group(1) or match.group(2)
                    if name and name not in known:
                        rel = template.relative_to(PROJECT_ROOT)
                        broken.setdefault(name, []).append(str(rel))

        assert not broken, "Unresolvable url tags: " + ", ".join(
            f"{name} ({len(files)}x, e.g. {files[0]})"
            for name, files in sorted(broken.items())
        )

    def test_doctor_availability_page_renders(self, client, db):
        """The page linked from the nav must not 500."""
        from staff.models import Staff

        user = User.objects.create_user("avail_user", password="pw")
        user.user_permissions.add(
            Permission.objects.get(codename="staff_view_staff")
        )
        Staff.objects.create(
            staff_id="DOC-AVAIL",
            first_name="Doc",
            last_name="Availability",
            role="DOCTOR",
            user=user,
        )
        client.force_login(user)

        response = client.get(reverse("doctor_availability"))
        assert response.status_code == 200


class TestPublicDemoAccountIsReadOnly:
    """The public demo account is advertised as a read-only sandbox.

    The credentials are published in the README, so the account must not be
    able to mutate data. Two independent mechanisms are asserted, because
    either alone leaks: the Staff role gates the API permission classes in
    ``core.permissions``, and group membership gates the view layer.
    """

    DEMO_PASSWORD = "demo1234"

    @pytest.fixture
    def demo_user(self, db):
        call_command("create_groups", verbosity=0)
        call_command("create_demo_user", force=True, verbosity=0)
        return User.objects.get(username="demo")

    def test_role_and_group_are_read_only(self, demo_user):
        assert demo_user.staff_profile.role == "VIEWER"
        assert [g.name for g in demo_user.groups.all()] == ["Demo Viewer"]

    def test_never_django_staff_or_superuser(self, demo_user):
        assert demo_user.is_staff is False
        assert demo_user.is_superuser is False

    def test_viewer_role_is_rejected_by_role_gated_api_classes(self):
        """A new role only isolates the demo account if it is absent from
        every allow-list. Adding it to one of these would silently re-open
        the API, so pin the guarantee explicitly."""
        from core.permissions import (
            IsAdminOrDoctor,
            IsAdminUser,
            IsBillingStaff,
            IsClinicalStaff,
            IsLabStaff,
            IsPharmacyStaff,
        )

        classes = [
            IsAdminUser,
            IsAdminOrDoctor,
            IsClinicalStaff,
            IsBillingStaff,
            IsLabStaff,
            IsPharmacyStaff,
        ]
        for permission_class in classes:
            allowed = getattr(permission_class, "ALLOWED_ROLES", None) or getattr(
                permission_class, "MEDICAL_ROLES", []
            )
            assert "VIEWER" not in allowed, (
                f"{permission_class.__name__} would grant the demo account API access"
            )

    def test_group_grants_no_write_permissions(self, demo_user):
        group = Group.objects.get(name="Demo Viewer")
        assert group.permissions.exists()
        for perm in group.permissions.all():
            codename = perm.codename
            for action in ("add", "change", "delete"):
                assert not codename.startswith(f"{action}_"), codename
                assert f"_{action}_" not in codename, codename

    def test_can_read_but_cannot_write(self, demo_user, client):
        client.force_login(demo_user)

        for url_name in ("patient_list", "appointment_list", "prescription_list"):
            assert client.get(reverse(url_name)).status_code == 200, url_name

        for url_name in ("patient_create", "appointment_create", "surgery_create"):
            assert client.get(reverse(url_name)).status_code == 403, url_name

    def test_api_endpoints_are_forbidden(self, api_client, demo_user):
        api_client.force_authenticate(user=demo_user)
        for url in ("/api/v1/patients/", "/api/v1/appointments/"):
            assert api_client.get(url).status_code == 403, url

    def test_django_admin_redirects_to_login(self, demo_user, client):
        client.force_login(demo_user)
        response = client.get("/admin/patients/patient/")
        assert response.status_code == 302
        assert "/admin/login/" in response.headers["Location"]

    def test_rerun_demotes_an_account_seeded_as_admin(self, demo_user):
        """Deployments created before this change hold ADMIN + the Admin group.

        ``get_or_create`` does not update an existing row, so without explicit
        demotion the published password would keep full write access forever.
        """
        staff = demo_user.staff_profile
        staff.role = "ADMIN"
        staff.save()
        demo_user.groups.clear()
        demo_user.groups.add(Group.objects.get(name="Admin"))

        call_command("create_demo_user", force=True, verbosity=0)

        staff.refresh_from_db()
        assert staff.role == "VIEWER"
        assert [g.name for g in demo_user.groups.all()] == ["Demo Viewer"]


class TestGroupPermissionResolution:
    """``create_groups`` must actually grant every permission it lists."""

    def test_underscored_app_labels_resolve(self, db):
        """App labels contain underscores, so splitting on the first "_"
        resolved care_monitoring and medical_records to bogus app labels and
        those permissions were silently skipped for every group."""
        call_command("create_groups", verbosity=0)
        assert Group.objects.get(name="Nurse").permissions.filter(
            codename="care_monitoring_view_patientcare"
        ).exists()
        assert Group.objects.get(name="Doctor").permissions.filter(
            codename="medical_records_view_document"
        ).exists()

    def test_django_default_codename_is_granted(self, db):
        """The bed map requires hospital.view_ward, which is a default
        permission named without the app prefix."""
        call_command("create_groups", verbosity=0)
        viewer = Group.objects.get(name="Demo Viewer")
        assert viewer.permissions.filter(codename="view_ward").exists()


class TestBedMapRenders:
    def test_occupancy_map_does_not_error(self, client, db):
        """``Room.ward`` declares no related_name, so the reverse accessor is
        ``room_set``. Prefetching a non-existent "rooms" raised AttributeError
        and 500'd the bed map for every user."""
        user = User.objects.create_user("bedmap_user", password="pw")
        user.user_permissions.add(Permission.objects.get(codename="view_ward"))
        client.force_login(user)

        response = client.get(reverse("hospital:occupancy_map"))
        assert response.status_code == 200
