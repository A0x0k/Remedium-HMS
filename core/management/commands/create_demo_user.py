"""
Creates a single, scoped demo account for public showcase deployments.

Unlike ``create_role_users``, this provisions exactly one read-only account.
It is never a Django superuser or staff user, so it cannot reach Django's
``/admin/`` site or the ``is_staff`` blanket bypass in ``core.permissions``.

Access is curtailed in two independent ways, because either one alone leaks:

1. Its Staff role is VIEWER, which appears in no ALLOWED_ROLES/MEDICAL_ROLES
   list in ``core.permissions``, so every role-gated API endpoint rejects it.
2. Its group holds only ``*_view_*`` permissions, so ``PermissionRequiredMixin``
   renders list and detail pages while every add/change/delete view 403s.

The command is opt-in: it refuses to run unless ``DEMO_ACCOUNT_ENABLED=true``
is set or ``--force`` is passed, so it can never be triggered accidentally.

It is safe to run on every deploy (idempotent) and never deletes data. It also
demotes an account seeded by an earlier version, so redeploying is what applies
a tightened role to an existing demo user.
"""

import os

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from decouple import config

from core.rbac import ROLE_GROUPS
from staff.models import Staff

TRUTHY = {"1", "true", "yes", "on"}

DEFAULT_USERNAME = "demo"
DEFAULT_PASSWORD = "demo1234"
DEFAULT_ROLE = "VIEWER"

PROTECTED_USERNAMES = {"admin", "root", "superuser"}


class Command(BaseCommand):
    help = (
        "Creates a single non-privileged demo account for public showcase "
        "deployments. Requires DEMO_ACCOUNT_ENABLED=true or --force."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Run even when DEMO_ACCOUNT_ENABLED is not set.",
        )
        parser.add_argument(
            "--if-enabled",
            action="store_true",
            help=(
                "Exit successfully without seeding when DEMO_ACCOUNT_ENABLED is "
                "unset. Use in deploy hooks so deployments without a demo "
                "account are not broken."
            ),
        )
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Reset the demo password even if the account already exists.",
        )

    def _check_enabled(self, options):
        """Return True if the caller explicitly opted in to demo seeding."""
        enabled = str(os.environ.get("DEMO_ACCOUNT_ENABLED", "")).strip().lower() in TRUTHY
        if options["force"] or enabled:
            return True
        if options["if_enabled"]:
            self.stdout.write(
                "DEMO_ACCOUNT_ENABLED is not set, skipping demo account creation."
            )
            return False
        raise CommandError(
            "Refusing to create a public demo account. Set "
            "DEMO_ACCOUNT_ENABLED=true or pass --force to proceed."
        )

    def _validate(self, username, role):
        """Reject reserved usernames, invalid roles, and pre-privileged accounts."""
        if username.lower() in PROTECTED_USERNAMES:
            raise CommandError(
                f"Refusing to seed demo credentials onto reserved username '{username}'."
            )

        valid_roles = {code for code, _ in Staff.ROLE_CHOICES}
        if role not in valid_roles:
            raise CommandError(
                f"Invalid DEMO_ROLE '{role}'. Expected one of: {', '.join(sorted(valid_roles))}"
            )

        existing = User.objects.filter(username=username).first()
        if existing and (existing.is_superuser or existing.is_staff):
            raise CommandError(
                f"User '{username}' already exists with elevated privileges. "
                "Refusing to attach a public demo password to it."
            )
        return existing

    def _revoke_privileges(self, user):
        """Guard against privilege drift on an account that predates this command."""
        if user.is_superuser or user.is_staff:
            user.is_superuser = False
            user.is_staff = False
            user.save(update_fields=["is_superuser", "is_staff"])
            self.stdout.write(self.style.WARNING("Revoked elevated privileges on demo user."))

    def _ensure_staff_profile(self, user, role):
        staff, created = Staff.objects.get_or_create(
            user=user,
            defaults={
                "staff_id": f"DEMO-{user.id:03d}",
                "first_name": "Demo",
                "last_name": "Viewer",
                "role": role,
                "department": "ADMINISTRATION",
                "phone": f"+1555000{user.id:04d}",
                "email": config("DEMO_EMAIL", default="demo@remedium.local"),
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created staff profile: {staff}"))
        elif staff.role != role:
            # An account seeded by an earlier version defaulted to ADMIN. The
            # role drives the API permission classes in core.permissions, so
            # it has to be corrected or the account stays privileged.
            previous = staff.role
            staff.role = role
            staff.save(update_fields=["role"])
            self.stdout.write(
                self.style.WARNING(
                    f"Demoted demo staff role from {previous} to {role}."
                )
            )
        else:
            self.stdout.write(f"Staff profile already exists: {staff}")

    def _assign_group(self, user, role):
        group_name = ROLE_GROUPS.get(role)
        if not group_name:
            return
        group = Group.objects.filter(name=group_name).first()
        if group:
            stale = user.groups.exclude(pk=group.pk)
            for extra in stale:
                user.groups.remove(extra)
                self.stdout.write(
                    self.style.WARNING(
                        f"Removed demo user from over-privileged group: {extra.name}"
                    )
                )
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f"Added to group: {group_name}"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Group '{group_name}' not found. Run create_groups first. "
                    "Navigation will still work via the staff profile role."
                )
            )

    def _report(self, username, password, reveal):
        self.stdout.write("")
        if not reveal:
            self.stdout.write(self.style.SUCCESS("Demo account already present. Nothing changed."))
            return
        self.stdout.write(self.style.WARNING("=" * 60))
        self.stdout.write(self.style.WARNING("Public demo credentials are now active."))
        self.stdout.write(self.style.WARNING(f"  username: {username}"))
        self.stdout.write(self.style.WARNING(f"  password: {password}"))
        self.stdout.write(
            self.style.WARNING(
                "This account is intentionally low-privilege. "
                "Rotate it if this is not a public demo."
            )
        )
        self.stdout.write(self.style.WARNING("=" * 60))

    def handle(self, *args, **options):
        if not self._check_enabled(options):
            return

        username = config("DEMO_USERNAME", default=DEFAULT_USERNAME)
        password = config("DEMO_PASSWORD", default=DEFAULT_PASSWORD)
        role = str(config("DEMO_ROLE", default=DEFAULT_ROLE)).strip().upper()

        existing = self._validate(username, role)
        created = existing is None
        reveal = created or options["reset_password"]

        if created:
            user = User.objects.create_user(
                username=username,
                email=config("DEMO_EMAIL", default="demo@remedium.local"),
                first_name="Demo",
                last_name="Viewer",
                is_staff=False,
                is_superuser=False,
            )
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created demo user: {username}"))
        else:
            user = existing
            if options["reset_password"]:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.WARNING(f"Reset demo password for: {username}"))
            else:
                self.stdout.write(
                    f"Demo user '{username}' already exists, leaving password untouched."
                )

        self._revoke_privileges(user)
        self._ensure_staff_profile(user, role)
        self._assign_group(user, role)
        self._report(username, password, reveal)
