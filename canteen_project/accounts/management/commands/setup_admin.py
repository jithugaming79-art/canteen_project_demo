"""
Management command to set superuser's UserProfile role to 'admin'.
Run after createsuperuser to ensure admin dashboard access.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Set superuser profile role to 'admin' for dashboard access"

    def handle(self, *args, **options):
        for user in User.objects.filter(is_superuser=True):
            profile, created = UserProfile.objects.get_or_create(user=user)
            if profile.role != 'admin':
                profile.role = 'admin'
                profile.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Set {user.username}'s role to 'admin'"
                ))
            else:
                self.stdout.write(f"{user.username} already has 'admin' role")
