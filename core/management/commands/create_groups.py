from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = "Creates default user groups and assigns permissions."

    def _resolve_permissions(self, perm_codename):
        """Resolve a permission string in this command's notation to Permissions.

        Two notations appear in the table above:

        * Custom permissions declared in a model Meta.permissions, whose
          codename is literally ``<app_label>_<action>_<name>``, e.g.
          ``patients_view_patient`` or ``medical_records_view_document``.
          Note the last one is declared on the PatientDocument model, so the
          trailing segment does not match the model name. The codename is the
          permission's identity, so match on it directly.
        * Django's auto-generated permissions, whose codename is just
          ``<action>_<model>`` (e.g. ``hospital.view_ward``). Views spell these
          with the app label prefix in ``permission_required``, which collides
          with the custom form above, so both candidates are returned and the
          caller grants each one that exists.

        A single entry can legitimately resolve to two distinct permissions,
        and granting both is what makes a group satisfy views regardless of
        which spelling they use.
        """
        found = []
        seen = set()

        def _add(perm):
            if perm is not None and perm.pk not in seen:
                seen.add(perm.pk)
                found.append(perm)

        _add(Permission.objects.filter(codename=perm_codename).first())

        # Django's auto-generated naming. App labels contain underscores
        # (care_monitoring, medical_records), so match the real app labels
        # longest-first rather than splitting on the first "_".
        app_labels = sorted(
            set(ContentType.objects.values_list("app_label", flat=True)),
            key=len,
            reverse=True,
        )
        for app_label in app_labels:
            prefix = f"{app_label}_"
            if not perm_codename.startswith(prefix):
                continue
            remainder = perm_codename[len(prefix) :]
            if "_" not in remainder:
                continue
            content_type = ContentType.objects.filter(
                app_label=app_label, model=remainder.split("_", 1)[1]
            ).first()
            if content_type is None:
                continue
            _add(
                Permission.objects.filter(
                    content_type=content_type, codename=remainder
                ).first()
            )
        return found

    def handle(self, *args, **kwargs):
        self.stdout.write("Creating default user groups...")

        # Define roles and their permissions
        roles = {
            "Admin": [
                "patients_view_patient",
                "patients_add_patient",
                "patients_change_patient",
                "patients_delete_patient",
                "staff_view_staff",
                "staff_add_staff",
                "staff_change_staff",
                "staff_delete_staff",
                "appointments_view_appointment",
                "appointments_add_appointment",
                "appointments_change_appointment",
                "appointments_delete_appointment",
                "billing_view_invoice",
                "billing_add_invoice",
                "billing_change_invoice",
                "billing_delete_invoice",
                "inventory_view_inventoryitem",
                "inventory_add_inventoryitem",
                "inventory_change_inventoryitem",
                "inventory_delete_inventoryitem",
                "laboratory_view_labtest",
                "laboratory_add_labtest",
                "laboratory_change_labtest",
                "laboratory_delete_labtest",
                "pharmacy_view_prescription",
                "pharmacy_add_prescription",
                "pharmacy_change_prescription",
                "pharmacy_delete_prescription",
                "reporting_view_report",
                "reporting_add_report",
                "reporting_change_report",
                "reporting_delete_report",
                "surgery_view_surgery",
                "surgery_add_surgery",
                "surgery_change_surgery",
                "surgery_delete_surgery",
                "care_monitoring_view_patientcare",
                "care_monitoring_add_patientcare",
                "care_monitoring_change_patientcare",
                "care_monitoring_delete_patientcare",
            ],
            "Doctor": [
                "patients_view_patient",
                "patients_change_patient",
                "appointments_view_appointment",
                "appointments_add_appointment",
                "appointments_change_appointment",
                "billing_view_invoice",
                "laboratory_view_labtest",
                "laboratory_add_labtest",
                "pharmacy_view_prescription",
                "pharmacy_add_prescription",
                "care_monitoring_view_patientcare",
                "care_monitoring_add_patientcare",
                "care_monitoring_change_patientcare",
                "surgery_view_surgery",
                "surgery_add_surgery",
                "surgery_change_surgery",
                "medical_records_view_document",
                "medical_records_add_document",
            ],
            "Nurse": [
                "patients_view_patient",
                "patients_change_patient",
                "appointments_view_appointment",
                "appointments_change_appointment",
                "billing_view_invoice",
                "care_monitoring_view_patientcare",
                "care_monitoring_add_patientcare",
                "care_monitoring_change_patientcare",
            ],
            "Receptionist": [
                "patients_view_patient",
                "patients_add_patient",
                "patients_change_patient",
                "appointments_view_appointment",
                "appointments_add_appointment",
                "appointments_change_appointment",
                "billing_view_invoice",
                "billing_add_invoice",
            ],
            "Pharmacist": [
                "patients_view_patient",
                "pharmacy_view_prescription",
                "pharmacy_change_prescription",
                "inventory_view_inventoryitem",
            ],
            "Lab Technician": [
                "patients_view_patient",
                "laboratory_view_labtest",
                "laboratory_change_labtest",
                "laboratory_add_labtest",
            ],
            # Read-only role backing the public demo account. Only *_view_*
            # codenames, so list and detail pages render but every create,
            # update and delete view raises PermissionDenied.
            "Demo Viewer": [
                "patients_view_patient",
                "medical_records_view_document",
                "appointments_view_appointment",
                "surgery_view_surgery",
                "care_monitoring_view_patientcare",
                "pharmacy_view_prescription",
                "laboratory_view_labtest",
                "hospital_view_ward",
                "hospital_view_hospitalservice",
            ],
        }

        for role_name, perms_list in roles.items():
            group, created = Group.objects.get_or_create(name=role_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Group '{role_name}' created."))
            else:
                self.stdout.write(f"Group '{role_name}' already exists.")

            # Clear existing permissions for the group before adding new ones
            group.permissions.clear()

            for perm_codename in perms_list:
                permissions = self._resolve_permissions(perm_codename)
                if not permissions:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Permission {perm_codename} not found. Skipping."
                        )
                    )
                    continue
                group.permissions.add(*permissions)

            self.stdout.write(
                self.style.SUCCESS(f"Permissions assigned to group '{role_name}'")
            )

        self.stdout.write(
            self.style.SUCCESS("Default user groups and permissions setup complete.")
        )
