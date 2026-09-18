"""
Social account adapter for Authentik (OIDC) logins.

- Existing, active staff accounts are matched by email and linked on first login.
- Members of the Authentik group AUTHENTIK_ADMIN_GROUP (default "openwisp-admins") who have no
  OpenWISP account yet are auto-created as superusers.
- Everyone else is refused. Nobody gets an account without being in the admin group.

Group membership comes from the "groups" claim (Authentik's default `profile` scope mapping).
It is only checked when an account is created; removing someone from the group later does NOT
demote or deactivate their OpenWISP account.
"""
import sys

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model


def _emails(sociallogin):
    emails = {a.email.lower() for a in sociallogin.email_addresses if a.email}
    if sociallogin.user.email:
        emails.add(sociallogin.user.email.lower())
    return emails


def _claims(sociallogin):
    """OIDC claims for this login as one flat dict.

    allauth >= 65.11 stores extra_data as {"userinfo": {...}, "id_token": {...}} (userinfo wins on
    conflicts); older versions stored the claims flat.
    """
    data = sociallogin.account.extra_data or {}
    merged = {}
    for key in ("id_token", "userinfo"):
        if isinstance(data.get(key), dict):
            merged.update(data[key])
    return merged or dict(data)


def _in_admin_group(sociallogin):
    group = getattr(settings, "AUTHENTIK_ADMIN_GROUP", "openwisp-admins")
    groups = _claims(sociallogin).get("groups") or []
    if isinstance(groups, str):
        groups = [groups]
    return group in groups


class AuthentikAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return
        User = get_user_model()
        for email in _emails(sociallogin):
            matches = list(
                User.objects.filter(email__iexact=email, is_active=True, is_staff=True)[:2]
            )
            if len(matches) == 1:
                # Link this Authentik identity to the matching OpenWISP account (no privilege change).
                sociallogin.connect(request, matches[0])
                return
        # No unique staff match: allauth falls through to signup (see is_open_for_signup).

    def is_open_for_signup(self, request, sociallogin):
        # Printed to stderr (shows up in the dashboard container logs) so a closed signup is explainable.
        who = sorted(_emails(sociallogin)) or ["<no email in claims>"]
        if not _in_admin_group(sociallogin):
            claims = _claims(sociallogin)
            print(
                "[oidc] signup closed for %s: not in group %r; groups claim=%r; claims present=%s"
                % (who, getattr(settings, "AUTHENTIK_ADMIN_GROUP", "openwisp-admins"),
                   claims.get("groups"), sorted(claims)),
                file=sys.stderr,
            )
            return False
        # Never create a second account for an email that is already in use.
        User = get_user_model()
        taken = [e for e in _emails(sociallogin) if User.objects.filter(email__iexact=e).exists()]
        if taken:
            print(
                "[oidc] signup closed for %s: an OpenWISP account already uses that email but is not "
                "an active staff user (or several accounts share it), so it was not linked" % (taken,),
                file=sys.stderr,
            )
            return False
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if _in_admin_group(sociallogin):
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])
        return user
