"""
Seed demo data management command.

Creates realistic demo data for testing and presentations.
Idempotent — safe to run multiple times without duplicates.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # Clear existing data first
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from patients.models import Patient
from staff.models import Staff
from appointments.models import Appointment
from billing.models import Invoice
from laboratory.models import LabTest
from pharmacy.models import Prescription
from surgery.models import Surgery
from care_monitoring.models import PatientCare
from hospital.models import Ward, Room


class Command(BaseCommand):
    help = "Seed the database with realistic demo data for testing and presentations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before seeding.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self._flush_data()

        now = timezone.now()
        admin_user = self._ensure_admin()

        self.stdout.write(self.style.SUCCESS("🏥 Seeding Remedium HMS demo data..."))

        # 1. Wards & Rooms
        wards = self._create_wards()
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✅ {Ward.objects.count()} wards, {Room.objects.count()} rooms"
            )
        )

        # 2. Staff
        staff_members = self._create_staff(admin_user)
        self.stdout.write(
            self.style.SUCCESS(f"  ✅ {len(staff_members)} staff members")
        )

        # 3. Patients
        patients = self._create_patients(wards)
        self.stdout.write(self.style.SUCCESS(f"  ✅ {len(patients)} patients"))

        # 4. Appointments
        appointments = self._create_appointments(patients, staff_members, now)
        self.stdout.write(self.style.SUCCESS(f"  ✅ {len(appointments)} appointments"))

        # 5. Lab Tests
        lab_tests = self._create_lab_tests(patients, staff_members, now)
        self.stdout.write(self.style.SUCCESS(f"  ✅ {len(lab_tests)} lab tests"))

        # 6. Prescriptions
        prescriptions = self._create_prescriptions(patients, staff_members, now)
        self.stdout.write(
            self.style.SUCCESS(f"  ✅ {len(prescriptions)} prescriptions")
        )

        # 7. Surgeries
        surgeries = self._create_surgeries(patients, staff_members, now)
        self.stdout.write(self.style.SUCCESS(f"  ✅ {len(surgeries)} surgeries"))

        # 8. Patient Care Records
        care_records = self._create_care_records(patients, staff_members, now)
        self.stdout.write(
            self.style.SUCCESS(f"  ✅ {len(care_records)} care monitoring records")
        )

        # 9. Invoices
        invoices = self._create_invoices(patients, now)
        self.stdout.write(self.style.SUCCESS(f"  ✅ {len(invoices)} invoices"))

        self.stdout.write(self.style.SUCCESS("\n🎉 Demo data seeding complete!"))
        self.stdout.write(
            self.style.WARNING(
                f"\n📊 Summary: "
                f"{Ward.objects.count()} wards, "
                f"{Room.objects.count()} rooms, "
                f"{Staff.objects.count()} staff, "
                f"{Patient.objects.count()} patients, "
                f"{Appointment.objects.count()} appointments, "
                f"{LabTest.objects.count()} lab tests, "
                f"{Prescription.objects.count()} prescriptions, "
                f"{Surgery.objects.count()} surgeries, "
                f"{PatientCare.objects.count()} care records, "
                f"{Invoice.objects.count()} invoices"
            )
        )

    def _flush_data(self):
        """Delete existing demo data."""
        self.stdout.write(self.style.WARNING("🗑️  Flushing existing demo data..."))
        PatientCare.objects.all().delete()
        Surgery.objects.all().delete()
        Prescription.objects.all().delete()
        LabTest.objects.all().delete()
        Appointment.objects.all().delete()
        Invoice.objects.all().delete()
        Patient.objects.all().delete()
        Staff.objects.exclude(staff_id="ADMIN_001").delete()
        Ward.objects.all().delete()
        Room.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("  ✅ Data flushed."))

    def _ensure_admin(self):
        """Ensure admin user and staff profile exist."""
        user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@remedium.test",
                "is_superuser": True,
                "is_staff": True,
            },
        )
        user.set_password("admin123")
        user.save()

        staff, _ = Staff.objects.get_or_create(
            staff_id="ADMIN_001",
            defaults={
                "user": user,
                "first_name": "System",
                "last_name": "Administrator",
                "role": "ADMIN",
                "department": "Administration",
            },
        )
        return staff

    def _create_wards(self):
        """Create hospital wards and rooms."""
        wards_data = [
            ("ICU", 10),
            ("Cardiology", 15),
            ("Pediatrics", 12),
            ("Orthopedics", 10),
            ("General Ward", 20),
        ]

        wards = []
        for name, capacity in wards_data:
            ward, _ = Ward.objects.get_or_create(
                name=name, defaults={"capacity": capacity}
            )
            wards.append(ward)

            # Create rooms
            prefix = name[:3].upper().replace(" ", "")
            for i in range(1, min(capacity // 2 + 1, 6)):
                Room.objects.get_or_create(
                    ward=ward,
                    room_number=f"{prefix}-{i:02d}",
                    defaults={
                        "capacity": random.choice([1, 2, 4]),
                    },
                )

        return wards

    def _create_staff(self, admin_staff):
        """Create staff members across all roles."""
        staff_data = [
            ("DOC_001", "Sarah", "Chen", "DOCTOR", "Cardiology"),
            ("DOC_002", "James", "Wilson", "DOCTOR", "Orthopedics"),
            ("DOC_003", "Maria", "Rodriguez", "DOCTOR", "Pediatrics"),
            ("NUR_001", "Emily", "Davis", "NURSE", "ICU"),
            ("NUR_002", "Michael", "Brown", "NURSE", "Cardiology"),
            ("NUR_003", "Anna", "Taylor", "NURSE", "Pediatrics"),
            ("REC_001", "David", "Martinez", "RECEPTIONIST", "Front Desk"),
            ("REC_002", "Lisa", "Anderson", "RECEPTIONIST", "Front Desk"),
            ("PHARM_001", "Robert", "Thomas", "PHARMACIST", "Pharmacy"),
            ("LAB_001", "Jennifer", "Jackson", "LAB_TECHNICIAN", "Laboratory"),
        ]

        staff_members = [admin_staff]
        for sid, first, last, role, dept in staff_data:
            staff, _ = Staff.objects.get_or_create(
                staff_id=sid,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "role": role,
                    "department": dept,
                    "phone": f"+1234567{random.randint(10, 99)}",
                    "email": f"{first.lower()}.{last.lower()}@remedium.test",
                    "is_active": True,
                },
            )
            staff_members.append(staff)

        return staff_members

    def _create_patients(self, wards):
        """Create patients with varied demographics."""
        first_names = [
            "John",
            "Emma",
            "Oliver",
            "Sophia",
            "William",
            "Isabella",
            "James",
            "Mia",
            "Benjamin",
            "Charlotte",
            "Lucas",
            "Amelia",
            "Henry",
            "Harper",
            "Alexander",
            "Evelyn",
            "Daniel",
            "Aria",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Jones",
            "Brown",
            "Davis",
            "Miller",
            "Wilson",
            "Moore",
            "Taylor",
            "Anderson",
            "Thomas",
        ]
        genders = ["M", "F"]
        conditions = [
            "Hypertension, Diabetes Type 2",
            "Fractured left tibia",
            "Pneumonia, recovering",
            "Post-operative knee replacement",
            "Routine checkup — no known conditions",
            "Asthma, seasonal allergies",
            "Appendicitis — emergency admission",
            "Cardiac arrhythmia monitoring",
            "Maternity — 36 weeks pregnant",
            "Gastroenteritis, dehydrated",
        ]

        patients = []
        for i in range(10):
            first = first_names[i]
            last = last_names[i]
            dob = timezone.now().date() - timedelta(
                days=random.randint(365 * 5, 365 * 80)
            )
            ward = random.choice(wards)
            ward_rooms = Room.objects.filter(ward=ward)
            room = random.choice(ward_rooms) if ward_rooms.exists() else None

            patient, _ = Patient.objects.get_or_create(
                unique_id=f"DEMO-{i+1:04d}",
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "date_of_birth": dob,
                    "gender": genders[i % 2],
                    "phone": f"+19876543{20+i:02d}",
                    "email": f"{first.lower()}.{last.lower()}@demo.test",
                    "address": f"{100+i} Demo Street, Demo City",
                    "medical_history": conditions[i],
                    "admission_date": timezone.now()
                    - timedelta(days=random.randint(1, 30)),
                    "ward": ward,
                    "room": room,
                },
            )
            patients.append(patient)

        return patients

    def _create_appointments(self, patients, staff_members, now):
        """Create past and upcoming appointments."""
        doctors = [s for s in staff_members if s.role == "DOCTOR"]
        statuses = ["Scheduled", "Completed", "Cancelled", "No Show"]

        appointments = []
        for i in range(20):
            doctor = random.choice(doctors)
            patient = random.choice(patients)

            if i < 10:
                # Past appointments
                appt_date = now - timedelta(
                    days=random.randint(1, 30), hours=random.randint(1, 12)
                )
                status = random.choice(
                    ["Completed", "Completed", "Completed", "Cancelled"]
                )
            else:
                # Future appointments
                appt_date = now + timedelta(
                    days=random.randint(1, 14), hours=random.randint(8, 16)
                )
                status = "Scheduled"

            appt, _ = Appointment.objects.get_or_create(
                patient=patient,
                doctor=doctor,
                appointment_date=appt_date,
                defaults={
                    "status": status,
                    "reason": random.choice(
                        [
                            "Follow-up consultation",
                            "Initial assessment",
                            "Post-surgery review",
                            "Routine checkup",
                            "Lab results discussion",
                        ]
                    ),
                },
            )
            appointments.append(appt)

        return appointments

    def _create_lab_tests(self, patients, staff_members, now):
        """Create lab test records."""
        tests = [
            ("Complete Blood Count (CBC)", "Hematology"),
            ("Lipid Panel", "Chemistry"),
            ("Thyroid Function Test", "Endocrinology"),
            ("Liver Function Test", "Chemistry"),
            ("Urinalysis", "Pathology"),
            ("HbA1c — Diabetes Screening", "Hematology"),
            ("X-Ray Chest PA", "Radiology"),
            ("ECG", "Cardiology"),
        ]
        statuses = ["Completed", "Pending", "In Progress", "Requested"]

        lab_tests = []
        for i, (test_name, category) in enumerate(tests):
            patient = patients[i % len(patients)]
            status = statuses[i % len(statuses)]

            lab_test, _ = LabTest.objects.get_or_create(
                patient=patient,
                test_name=test_name,
                defaults={
                    "status": status,
                    "requested_date": now - timedelta(days=random.randint(1, 14)),
                },
            )
            lab_tests.append(lab_test)

        return lab_tests

    def _create_prescriptions(self, patients, staff_members, now):
        """Create prescription records."""
        drugs = [
            ("Amoxicillin", "500mg", "3 times daily"),
            ("Ibuprofen", "400mg", "Every 6 hours as needed"),
            ("Metformin", "500mg", "Twice daily with meals"),
            ("Lisinopril", "10mg", "Once daily in the morning"),
            ("Omeprazole", "20mg", "Once daily before breakfast"),
            ("Salbutamol Inhaler", "100mcg/puff", "2 puffs every 4-6 hours"),
            ("Atorvastatin", "20mg", "Once daily at bedtime"),
            ("Paracetamol", "500mg", "Every 4-6 hours as needed"),
        ]

        doctors = [s for s in staff_members if s.role == "DOCTOR"]
        prescriptions = []
        for i, (drug, dosage, freq) in enumerate(drugs):
            patient = patients[i % len(patients)]
            doctor = random.choice(doctors)

            rx, _ = Prescription.objects.get_or_create(
                patient=patient,
                drug_name=drug,
                defaults={
                    "dosage": dosage,
                    "frequency": freq,
                    "prescribed_by": doctor,
                    "notes": f"Demo prescription #{i+1}",
                },
            )
            prescriptions.append(rx)

        return prescriptions

    def _create_surgeries(self, patients, staff_members, now):
        """Create surgery records."""
        surgeries_data = [
            ("Appendectomy", "OR-1", "Emergency surgery for acute appendicitis"),
            ("Knee Replacement", "OR-2", "Total knee arthroplasty — right knee"),
            ("Cataract Removal", "OR-3", "Phacoemulsification with IOL implant"),
            ("Hernia Repair", "OR-1", "Laparoscopic inguinal hernia repair"),
        ]

        doctors = [s for s in staff_members if s.role == "DOCTOR"]
        surgeries = []
        for i, (procedure, room, notes) in enumerate(surgeries_data):
            patient = patients[i % len(patients)]
            surgeon = doctors[i % len(doctors)]

            surgery, _ = Surgery.objects.get_or_create(
                patient=patient,
                surgeon=surgeon,
                scheduled_date=now + timedelta(days=random.randint(1, 30)),
                operating_room=room,
                defaults={
                    "procedure": procedure,
                    "status": "Scheduled",
                    "notes": notes,
                },
            )
            surgeries.append(surgery)

        return surgeries

    def _create_care_records(self, patients, staff_members, now):
        """Create patient care monitoring records."""
        nurses = [s for s in staff_members if s.role == "NURSE"]
        statuses = ["STABLE", "CRITICAL", "IMPROVING", "OBSERVATION"]

        records = []
        for i, patient in enumerate(patients[:6]):
            nurse = random.choice(nurses)

            care, _ = PatientCare.objects.get_or_create(
                patient=patient,
                monitored_by=nurse,
                monitoring_date=now - timedelta(hours=i * 8),
                defaults={
                    "status": statuses[i % len(statuses)],
                    "temperature": round(random.uniform(36.0, 39.5), 1),
                    "heart_rate": random.randint(60, 110),
                    "blood_pressure_systolic": random.randint(110, 160),
                    "blood_pressure_diastolic": random.randint(60, 95),
                    "oxygen_saturation": round(random.uniform(92.0, 99.5), 1),
                    "weight": round(random.uniform(50.0, 100.0), 1),
                    "height": round(random.uniform(150.0, 185.0), 1),
                },
            )
            records.append(care)

        return records

    def _create_invoices(self, patients, now):
        """Create invoice records with varied payment status."""
        invoice_data = [
            (150.00, "General consultation and lab work"),
            (500.00, "Emergency room visit and X-ray"),
            (2500.00, "Knee replacement surgery"),
            (75.00, "Routine blood tests"),
            (300.00, "Cardiology consultation and ECG"),
            (1200.00, "Maternity package — prenatal care"),
            (450.00, "Appendectomy surgery"),
            (200.00, "Physical therapy sessions (5)"),
        ]

        invoices = []
        for i, (amount, description) in enumerate(invoice_data):
            patient = patients[i % len(patients)]
            is_paid = i < 4  # First 4 are paid

            invoice = Invoice.objects.create(
                patient=patient,
                total_amount=amount,
                paid=is_paid,
            )
            invoices.append(invoice)

        return invoices
