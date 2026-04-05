# Stickpile Compose Stack Inventory

All stacks are deployed via [DocoCD](https://github.com/pcs3rd/stickpile_doco-cd) from the `prod` branch.
Secrets are managed via SOPS-encrypted `secrets.enc.env` files per stack.
All externally accessible services are routed through Traefik on `traefik_backbone` using HTTPS (`websecure` entrypoint, `httpsResolve` cert resolver).

> ⚙️ Container versions in this file are automatically updated by GitHub Actions on every push to `prod`.
> Last updated: <!-- LAST-UPDATED -->2026-04-05 00:55 UTC<!-- /LAST-UPDATED -->

---

## Deployment Targets

| DocoCD File | Purpose |
|---|---|
| `.doco-cd.us-east-stickpile-prod.yaml` | Main application stacks |
| `.doco-cd.us-east-network-prod.yaml` | Network/infrastructure stacks |

---

## Core Services

### `traefik` · `core_services/traefik`
> Reverse proxy, TLS termination, CrowdSec security, and OpenTelemetry tracing.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:core_services/traefik -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `traefik` | `traefik` | `v3.5.3` | `traefik_backbone` | ❌ |
| `crowdsec` | `crowdsecurity/crowdsec` | `v1.7.4-debian` | `traefik_backbone` | ❌ |
| `otel-collector` | `otel/opentelemetry-collector-contrib` | `latest` | *(none defined)* | ❌ |
<!-- /STACK-TABLE:core_services/traefik -->

---

### `authentik` · `core_services/authentik`
> Identity provider and SSO. Used as the forward-auth middleware for most services.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:core_services/authentik -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `postgresql` | `docker.io/library/postgres` | `16-alpine` | `authentik` | ❌ |
| `authentik` | `ghcr.io/goauthentik/server` | `$AUTHENTIK_TAG` | `authentik`, `traefik_backbone` | ✅ (`postgresql`) |
| `worker` | `ghcr.io/goauthentik/server` | `$AUTHENTIK_TAG` | `authentik`, `traefik_backbone` | ✅ (`postgresql`) |
<!-- /STACK-TABLE:core_services/authentik -->

---

### `monitoring` · `core_services/monitoring`
> Log aggregation and alerting. Promtail auto-discovers all Docker containers via the socket — no per-service changes needed. Grafana is SSO-integrated with Authentik.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:core_services/monitoring -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `loki` | `grafana/loki` | `latest` | `monitoring` | ❌ |
| `promtail` | `grafana/promtail` | `latest` | `monitoring` | ✅ (`loki`) |
| `grafana` | `grafana/grafana` | `latest` | `monitoring`, `traefik_backbone` | ✅ (`loki`) |
<!-- /STACK-TABLE:core_services/monitoring -->

---

### `ubiquity-console` · `core_services/networking/ubnt_console`
> Unifi Network Application and MongoDB backend for managing Ubiquiti network hardware.
> In DocoCD (`us-east-network-prod`): ✅

<!-- STACK-TABLE:core_services/networking/ubnt_console -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `unifi-network-application` | `lscr.io/linuxserver/unifi-network-application` | `10.1.89` | *(none defined)* | ❌ |
| `mongo` | `docker.io/mongo` | `8.2.2` | *(none defined)* | ❌ |
| `mongo-express` | `mongo-express` | `latest` | *(none defined)* | ❌ |
<!-- /STACK-TABLE:core_services/networking/ubnt_console -->

---

### `blocky` · `core_services/networking/blocky`
> LAN-facing DNS server with ad/tracker blocking and query logging.
> In DocoCD (`us-east-network-prod`): ✅

<!-- STACK-TABLE:core_services/networking/blocky -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `blocky` | `spx01/blocky` | `latest` | *(none defined)* | ✅ (`redis`) |
| `redis` | `redis` | `6.2-alpine` | *(none defined)* | ❌ |
| `ui` | `ghcr.io/gabeduartem/blocky-ui` | `latest` | *(none defined)* | ✅ (`blocky`) |
<!-- /STACK-TABLE:core_services/networking/blocky -->

---

## Network Services

### `blocky-tailscale` · `network-services/blocky-tailscale`
> Tailscale-networked Blocky DNS instance. Blocky runs in the Tailscale container's network namespace so it is only reachable over the tailnet.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:network-services/blocky-tailscale -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `tailscale` | `tailscale/tailscale` | `latest` | `internal` | ❌ |
| `redis` | `redis` | `6.2-alpine` | `internal` | ❌ |
| `blocky` | `spx01/blocky` | `latest` | `service:tailscale` (network_mode) | ✅ (`tailscale`, `redis`) |
| `blocky-ui` | `ghcr.io/gabeduartem/blocky-ui` | `latest` | `internal`, `traefik_backbone` | ✅ (`blocky`) |
<!-- /STACK-TABLE:network-services/blocky-tailscale -->

---

## Web Apps

### `media_server` · `web-apps/jellyfin`
> Full media server stack including Jellyfin, Immich, *arr suite, download clients, and media management tools.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:web-apps/jellyfin -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `tinshop` | `ghcr.io/ajmandourah/tinshop-ng` | `v0.5.3` | `traefik_backbone`, `mediaserver` | ❌ |
| `ariang` | `hurlenko/aria2-ariang` | `1.3.13` | `traefik_backbone`, `mediaserver` | ❌ |
| `bazarr` | `lscr.io/linuxserver/bazarr` | `1.5.6` | `traefik_backbone`, `mediaserver` | ❌ |
| `flaresolverr` | `ghcr.io/flaresolverr/flaresolverr` | `v3.4.6` | `mediaserver` | ❌ |
| `immich-database` | `docker.io/tensorchord/pgvecto-rs` | `pg14-v0.2.0` | `mediaserver` | ❌ |
| `immich-machine-learning` | `ghcr.io/immich-app/immich-machine-learning` | `$IMMICH_VERSION` | `mediaserver` | ❌ |
| `immich-redis` | `docker.io/redis` | `6.2-alpine` | `mediaserver` | ❌ |
| `immich-server` | `ghcr.io/immich-app/immich-server` | `$IMMICH_VERSION` | `traefik_backbone`, `mediaserver` | ✅ (`immich-database`, `immich-redis`) |
| `jellyfin` | `lscr.io/linuxserver/jellyfin` | `10.11.6` | `mediaserver`, `traefik_backbone` | ❌ |
| `jellyseerr` | `seerr/seerr` | `v3.1.0` | `traefik_backbone`, `mediaserver` | ❌ |
| `calibre` | `lscr.io/linuxserver/calibre` | `latest` | `traefik_backbone` | ❌ |
| `komga` | `ghcr.io/gotson/komga` | `1.24.3` | `traefik_backbone`, `mediaserver` | ❌ |
| `navidrome` | `deluan/navidrome` | `0.60.3` | `mediaserver`, `traefik_backbone` | ❌ |
| `prowlarr` | `lscr.io/linuxserver/prowlarr` | `2.3.0` | `traefik_backbone`, `mediaserver` | ❌ |
| `radarr` | `lscr.io/linuxserver/radarr` | `6.0.4` | `traefik_backbone`, `mediaserver` | ❌ |
| `rdtclient` | `rogerfar/rdtclient` | `2.0.125` | `traefik_backbone`, `mediaserver` | ❌ |
| `chaptarr` | `robertlordhood/chaptarr` | `latest` | `traefik_backbone`, `mediaserver` | ❌ |
| `sonarr` | `lscr.io/linuxserver/sonarr` | `4.0.16` | `traefik_backbone`, `mediaserver` | ❌ |
| `tvheadend` | `ghcr.io/linuxserver/tvheadend` | `version-7c4011de` | `host` (network_mode) | ❌ |
| `tdarr` | `ghcr.io/haveagitgat/tdarr` | `latest` | `bridge` (network_mode) | ❌ |
| `lidarr` | `lscr.io/linuxserver/lidarr` | `3.1.0` | `traefik_backbone`, `mediaserver` | ❌ |
| `metube` | `ghcr.io/alexta69/metube` | `2026.03.08` | `traefik_backbone`, `mediaserver` | ❌ |
| `soularr` | `mrusse08/soularr` | `latest` | `mediaserver` | ❌ |
| `slskd` | `slskd/slskd` | `0.24.5` | `traefik_backbone`, `mediaserver` | ❌ |
| `bliss_service` | `romancin/bliss` | `latest` | `traefik_backbone`, `mediaserver` | ❌ |
| `ersatztv` | `ghcr.io/ersatztv/ersatztv` | `latest` | `mediaserver` | ❌ |
| `rsoul` | `ghcr.io/pcs3rd/rsoul` | `release.rate-limit-test` | `mediaserver` | ❌ |
<!-- /STACK-TABLE:web-apps/jellyfin -->

---

### `seafile` · `web-apps/seafile`
> Self-hosted file sync and share with WebDAV support.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:web-apps/seafile -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `db` | `mariadb` | `10.11` | `internal` | ❌ |
| `memcached` | `memcached` | `1.6.18` | `internal` | ❌ |
| `seafile` | `seafileltd/seafile-mc` | `11.0-latest` | `internal`, `backbone` | ✅ (`db`, `memcached`) |
<!-- /STACK-TABLE:web-apps/seafile -->

---

### `affine` · `web-apps/affine`
> Collaborative knowledge base / whiteboard workspace.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:web-apps/affine -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `affine` | `ghcr.io/toeverything/affine` | `$AFFINE_REVISION` | `internal`, `traefik_backbone` | ❌ |
| `affine_migration` | `ghcr.io/toeverything/affine` | `$AFFINE_REVISION` | `internal` | ❌ |
| `redis` | `redis` | `latest` | `internal` | ❌ |
| `postgres` | `pgvector/pgvector` | `pg16` | `internal` | ❌ |
<!-- /STACK-TABLE:web-apps/affine -->

---

### `kiwix` · `web-apps/kiwix`
> Offline Wikipedia, Gutenberg, iFixit, CDC, and other ZIM archive server.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:web-apps/kiwix -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `kiwix-server` | `ghcr.io/kiwix/kiwix-serve` | `latest` | `traefik_backbone` | ❌ |
<!-- /STACK-TABLE:web-apps/kiwix -->

---

### `meshtastic` · `web-apps/meshtastic`
> Meshtastic daemon and mesh bot for LoRa radio mesh networking.
> In DocoCD (`us-east-stickpile-prod`): ✅

<!-- STACK-TABLE:web-apps/meshtastic -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `meshing-around` | `ghcr.io/spudgunman/meshing-around` | `main` | `mesh-internal` | ❌ |
| `meshtasticd` | `meshtastic/meshtasticd` | `2.7.15.d18f3f7-beta-alpine` | `mesh-internal` | ❌ |
<!-- /STACK-TABLE:web-apps/meshtastic -->

---

### `mixpost` · `web-apps/mixpost`
> Social media scheduling and management. ⚠️ Currently commented out in DocoCD.
> In DocoCD (`us-east-stickpile-prod`): ❌ *(commented out)*

<!-- STACK-TABLE:web-apps/mixpost -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `mixpost` | `inovector/mixpost` | `latest` | `internal`, `traefik_backbone` | ✅ (`mysql`, `redis`) |
| `mysql` | `mysql/mysql-server` | `8.0` | `internal` | ❌ |
| `redis` | `redis` | `latest` | `internal` | ❌ |
<!-- /STACK-TABLE:web-apps/mixpost -->

---

### `wordpress` · `web-apps/wordpress`
> WordPress site (raymonddean.me). Not present in either DocoCD file.
> In DocoCD: ❌

<!-- STACK-TABLE:web-apps/wordpress -->
| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `wpdb` | `mariadb` | `10.6.4-focal` | `internal` | ❌ |
| `wordpress` | `wordpress` | `latest` | `internal`, `traefik_backbone` | ❌ |
<!-- /STACK-TABLE:web-apps/wordpress -->

---

## Network Overview

| Network Name | Type | Used By |
|---|---|---|
| `traefik_backbone` | External (shared) | All Traefik-exposed services |
| `core-prod-authentik_Internal` | Bridge | authentik stack internal |
| `core-prod-monitoring_internal` | Bridge | monitoring stack internal |
| `web-prod-media-server_Internal` | Bridge | media_server stack internal |
| `web-prod-seafile_Internal` | Bridge | seafile stack internal |
| `web-prod-affine_Internal` | Bridge | affine stack internal |
| `web-prod-kiwix_Internal` | Bridge | *(commented out)* |
| `web-prod-meshtastic_Internal` | Bridge | meshtastic stack internal |
| `web-prod-blocky_Internal` | Bridge | blocky-tailscale stack internal |
| `web-prod-mixpost_Internal` | Bridge | mixpost stack internal |
| `web-prod-wordpress_Internal` | Bridge | wordpress stack internal |
