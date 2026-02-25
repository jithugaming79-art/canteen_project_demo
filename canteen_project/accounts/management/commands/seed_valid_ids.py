"""
Management command to seed ValidStudent and ValidStaff entries.
Add registration numbers here so they are available for user signup.
"""
from django.core.management.base import BaseCommand
from accounts.models import ValidStudent, ValidStaff


class Command(BaseCommand):
    help = "Seed valid student and staff registration numbers"

    def handle(self, *args, **options):
        # ========== ADD STUDENT REGISTRATION NUMBERS HERE ==========
        student_ids = [
            '03SU23FC102',
            '03SU23FC071',
            '03SU23FC001',
            '03SU23FC002',
            '03SU23FC003',
            '03SU23FC004',
            '03SU23FC005',
        ]

        # ========== ADD STAFF / FACULTY IDS HERE ==========
        staff_ids = [
            '03SU26SI001',
            '03SU26FI001',
        ]

        # Seed students
        created_count = 0
        for reg_no in student_ids:
            obj, created = ValidStudent.objects.get_or_create(register_no=reg_no)
            if created:
                created_count += 1
                self.stdout.write(f"  + Added student: {reg_no}")
            else:
                self.stdout.write(f"  = Already exists: {reg_no}")

        self.stdout.write(self.style.SUCCESS(
            f"Students: {created_count} new, {len(student_ids) - created_count} existing"
        ))

        # Seed staff
        created_count = 0
        for staff_id in staff_ids:
            obj, created = ValidStaff.objects.get_or_create(staff_id=staff_id)
            if created:
                created_count += 1
                self.stdout.write(f"  + Added staff: {staff_id}")
            else:
                self.stdout.write(f"  = Already exists: {staff_id}")

        self.stdout.write(self.style.SUCCESS(
            f"Staff: {created_count} new, {len(staff_ids) - created_count} existing"
        ))
