"""
Extra Django settings for OpenWISP (mounted at /opt/openwisp/openwisp/configuration).

Adds "Log in with Authentik" (OpenID Connect via django-allauth) to the admin.
Nothing here is active until OIDC_CLIENT_ID and OIDC_CLIENT_SECRET are set in secrets.enc.env.

This file is star-imported at the very end of openwisp/settings.py, so it cannot see the
settings defined above it directly. We reach them through the half-loaded settings module,
and mutate INSTALLED_APPS / SOCIALACCOUNT_PROVIDERS in place. Names defined in this file
(SOCIALACCOUNT_ADAPTER, ...) are applied by the star import as usual.

NOTE: settings.py wraps the import in `except ImportError: pass`, so an ImportError in here
is silent. If SSO does nothing, check the container logs for the "[oidc]" message below.
"""
import os
import sys

_client_id = os.environ.get("OIDC_CLIENT_ID", "")
_client_secret = os.environ.get("OIDC_CLIENT_SECRET", "")
# allauth appends "/.well-known/openid-configuration" itself, so a trailing slash would give "//".
_server_url = os.environ.get("OIDC_SERVER_URL", "").rstrip("/")
_base = sys.modules.get("openwisp.settings")

if _client_id and _client_secret and _server_url:
    if _base is None:
        print("[oidc] openwisp.settings not found in sys.modules, Authentik login disabled", file=sys.stderr)
    else:
        for _app in (
            "allauth.socialaccount",
            "allauth.socialaccount.providers.openid_connect",
        ):
            if _app not in _base.INSTALLED_APPS:
                _base.INSTALLED_APPS.append(_app)

        # Keeps the existing facebook/google entries used by openwisp-radius.
        _base.SOCIALACCOUNT_PROVIDERS["openid_connect"] = {
            "OAUTH_PKCE_ENABLED": True,
            "APPS": [
                {
                    "provider_id": "authentik",
                    "name": "Authentik",
                    "client_id": _client_id,
                    "secret": _client_secret,
                    "settings": {"server_url": _server_url},
                }
            ],
        }

        # Existing staff are linked by email; members of the admin group are auto-created as superusers.
        SOCIALACCOUNT_ADAPTER = "openwisp.configuration.authentik_oidc.AuthentikAdapter"
        AUTHENTIK_ADMIN_GROUP = os.environ.get("OIDC_ADMIN_GROUP", "openwisp-admins")
        # Authentik reports email_verified=false by default; don't block social signups on it.
        SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
        # Lets /accounts/oidc/authentik/login/ redirect straight to Authentik (bookmarkable).
        SOCIALACCOUNT_LOGIN_ON_GET = True
        # TLS ends at Traefik and nginx serves plain HTTP, so force https in the callback URL.
        ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
