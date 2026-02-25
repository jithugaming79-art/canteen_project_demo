"""
Management command to set superuser's UserProfile role to 'admin'
and create a kitchen staff user if env vars are set.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = "Set superuser profile role to 'admin' and create kitchen user"

    def handle(self, *args, **options):
        # Set all superusers to admin role
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

        # Create kitchen user if env vars are set
        kitchen_user = os.environ.get('KITCHEN_USERNAME', '')
        kitchen_pass = os.environ.get('KITCHEN_PASSWORD', '')
        if kitchen_user and kitchen_pass:
            user, created = User.objects.get_or_create(
                username=kitchen_user,
                defaults={'is_staff': True}
            )
            if created:
                user.set_password(kitchen_pass)
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Created kitchen user: {kitchen_user}"
                ))
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if profile.role != 'kitchen':
                profile.role = 'kitchen'
                profile.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Set {kitchen_user}'s role to 'kitchen'"
                ))

