## OpenWISP
----
Network controller for OpenWrt devices: config templates, monitoring, RADIUS, firmware upgrades and a management VPN.
Upstream: https://github.com/openwisp/docker-openwisp (compose adapted from tag 25.10.4).

- Dashboard: https://wisp.stickpile.net (admin at `/admin/`)
- API: https://wisp-api.stickpile.net
- Both are routed by Traefik to the `nginx` container (`SSL_CERT_MODE=External`, plain HTTP inside).
- **DNS-only** record `wisp-vpn.stickpile.net` -> this host. Not proxied.
- Host ports to forward/open: `1194/udp` (management VPN), `1812/udp` + `1813/udp` (RADIUS).

### Secrets
`secrets.enc.env` (sops, dotenv) must define: `DJANGO_SECRET_KEY`, `DB_USER`, `DB_PASS`, `INFLUXDB_USER`, `INFLUXDB_PASS`.
Optional: `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` (Authentik login, see below), `X509_COUNTRY_CODE`, `X509_STATE`, `X509_CITY`, `OPENWISP_SUBNET`, `OPENWISP_VERSION`.

### Before first deploy
1. Create these directories on the NFS server: `<appdata>/openwisp/media` and `<appdata>/openwisp/private`.
2. Make sure `172.29.240.0/24` (or whatever `OPENWISP_SUBNET` is set to) is unused on the host. FreeRADIUS API access is restricted to this subnet.
3. Check that the first-boot superuser password was changed (upstream seeds a default `admin` account).

### Login with Authentik (OIDC)
OpenWISP has no built-in OAuth/OIDC for its admin, so this uses django-allauth's `openid_connect` provider through
`configuration/custom_django_settings.py` (mounted into the Django containers). It stays off until `OIDC_CLIENT_ID` and
`OIDC_CLIENT_SECRET` are set in `secrets.enc.env`.

Set up in Authentik:
1. Applications > Providers > create an **OAuth2/OpenID Provider**: client type *Confidential*, redirect URI (strict)
   `https://wisp.stickpile.net/accounts/oidc/authentik/login/callback/`, scopes `openid` `email` `profile`, and a signing key (RS256).
2. Applications > create an application with slug **`openwisp`** (must match `OIDC_SERVER_URL` in `compose.yaml`) using that provider.
   Restrict who can open it with a group policy.
3. Copy the client ID and secret into `secrets.enc.env` as `OIDC_CLIENT_ID` / `OIDC_CLIENT_SECRET`.

Then sign in at `https://wisp.stickpile.net/accounts/oidc/authentik/login/` (bookmark it; the normal admin login page has no button).

How it behaves:
- Only **existing, active staff** OpenWISP users can sign in this way. The Authentik email must match the OpenWISP user's email; the
  first login links the two. No accounts are ever created from an Authentik login.
- Anyone who can set their own email in Authentik to an admin's address can sign in as that admin. Disable self-service email edits there.
- The normal username/password login still works as a fallback.
- `settings.py` swallows `ImportError` from the custom settings, so failures are silent. Look for `[oidc]` in the container logs.
- `allauth.socialaccount` may need database migrations on first start; the dashboard container runs them at boot.

### Troubleshooting
- Login/POST fails with a CSRF error: nginx is probably not forwarding `X-Forwarded-Proto: https` from Traefik.
- Postfix sends directly from this host; set up a relay if mail gets rejected.
