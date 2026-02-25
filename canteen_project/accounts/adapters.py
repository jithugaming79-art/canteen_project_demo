from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .models import UserProfile

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        
        # Ensure profile exists and populate from social data
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        extra_data = sociallogin.account.extra_data
        
        # Get name from social account (Google/Facebook structure varies slightly but 'name' is common)
        if 'name' in extra_data:
            profile.full_name = extra_data.get('name', '')
        elif 'given_name' in extra_data:
            # Google often provides this breakdown
            first = extra_data.get('given_name', '')
            last = extra_data.get('family_name', '')
            profile.full_name = f"{first} {last}".strip()
        
        profile.save()
        return user
