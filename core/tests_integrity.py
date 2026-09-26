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
from django.contrib.auth.models import Group, Permission
from django.urls import get_resolver, reverse, NoReverseMatch

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
        from django.contrib.auth.models import User
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
