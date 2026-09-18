"""Social account adapter: Authentik may only sign in to OpenWISP staff accounts that already exist."""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class ExistingStaffOnlyAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        # Never create OpenWISP accounts from an Authentik login.
        return False

    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        emails = {a.email.lower() for a in sociallogin.email_addresses if a.email}
        if sociallogin.user.email:
            emails.add(sociallogin.user.email.lower())
        User = get_user_model()
        for email in emails:
            matches = list(
                User.objects.filter(email__iexact=email, is_active=True, is_staff=True)[:2]
            )
            if len(matches) == 1:
                # Link this Authentik identity to the matching OpenWISP account.
                sociallogin.connect(request, matches[0])
                return
        # No unique staff match: allauth falls through to signup, which is closed above.
