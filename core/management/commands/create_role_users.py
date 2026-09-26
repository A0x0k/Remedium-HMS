import secrets
import string
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, User

from core.rbac import ROLE_GROUPS
from staff.models import Staff


ROLES = [
    ("admin", "ADMIN", "ADMINISTRATION", "Admin", "Admin"),
    ("doctor", "DOCTOR", "CARDIOLOGY", "John", "Doe"),
    ("nurse", "NURSE", "ICU", "Jane", "Smith"),
    ("surgeon", "SURGEON", "SURGERY", "Robert", "Brown"),
    ("anesthesiologist", "ANESTHESIOLOGIST", "SURGERY", "Emily", "Davis"),
    ("radiologist", "RADIOLOGIST", "RADIOLOGY", "Michael", "Wilson"),
    ("receptionist", "RECEPTIONIST", "EMERGENCY", "Sarah", "Taylor"),
    ("pharmacist", "PHARMACIST", "PHARMACY", "David", "Anderson"),
    ("labtech", "LAB_TECH", "LABORATORY", "Lisa", "Thomas"),
    ("technician", "TECH", "OTHER", "James", "Jackson"),
    ("security", "SECURITY", "SECURITY", "Chris", "Martin"),
    ("maintenance", "MAINTENANCE", "MAINTENANCE", "Alex", "White"),
    ("other", "OTHER", "OTHER", "Sam", "Moore"),
]


def generate_password(length=16):
    """Generate a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class Command(BaseCommand):
    help = "Creates one user + staff profile per role with a random password"

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-default-password',
            action='store_true',
            help='Use default password "password123" instead of generating random ones (INSECURE, for demo only)',
        )

    def handle(self, *args, **options):
        use_default = options['use_default_password']
        if use_default:
            self.stdout.write(self.style.WARNING(
                'Using default password "password123" - NOT recommended for any environment'
            ))
            password = "password123"
        else:
            password = generate_password()

        created_count = 0
        exists_count = 0
        credentials = []

        for username, role_code, department, first_name, last_name in ROLES:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@remedium.local",
                },
            )
            if created:
                user.set_password(password)
                user.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created user: {username}"))
            else:
                exists_count += 1

            staff_id = f"{role_code[:4].upper()}-{user.id:03d}"
            Staff.objects.get_or_create(
                user=user,
                defaults={
                    "staff_id": staff_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "role": role_code,
                    "department": department,
                    "phone": f"+1555{user.id:07d}",
                    "email": f"{username}@remedium.local",
                    "is_active": True,
                },
            )

            # Group membership is what makes user.has_perm(...) resolve.
            # Without it the seeded accounts rely solely on staff_profile.role.
            group_name = ROLE_GROUPS.get(role_code)
            group = Group.objects.filter(name=group_name).first() if group_name else None
            if group:
                user.groups.add(group)
            else:
                self.stdout.write(self.style.WARNING(
                    f"Group '{group_name}' not found for '{username}'. Run create_groups first."
                ))

            credentials.append((username, role_code))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {created_count} users created, {exists_count} already existed."
        ))

        if created_count > 0:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("=" * 60))
            self.stdout.write(self.style.WARNING("IMPORTANT: Save these credentials securely!"))
            self.stdout.write(self.style.WARNING(f"Password for all new users: {password}"))
            self.stdout.write(self.style.WARNING("=" * 60))
            self.stdout.write("")
            self.stdout.write("Available accounts:")
            for username, role_code in credentials:
                self.stdout.write(f"  {username:<20} ({role_code})")
        else:
            self.stdout.write("No new users were created (all already exist).")
