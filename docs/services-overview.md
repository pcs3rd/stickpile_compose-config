# Stickpile Compose Stack Inventory

All stacks are deployed via [DocoCD](https://github.com/pcs3rd/stickpile_doco-cd) from the `prod` branch.
Secrets are managed via SOPS-encrypted `secrets.enc.env` files per stack.
All externally accessible services are routed through Traefik on `traefik_backbone` using HTTPS (`websecure` entrypoint, `httpsResolve` cert resolver).

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

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `traefik` | `traefik` | `v3.5.3` | `traefik_backbone` | ❌ |
| `crowdsec` | `crowdsecurity/crowdsec` | `v1.7.4-debian` | `traefik_backbone` | ❌ |
| `otel-collector` | `otel/opentelemetry-collector-contrib` | `latest` | *(none defined)* | ❌ |

---

### `authentik` · `core_services/authentik`
> Identity provider and SSO. Used as the forward-auth middleware for most services.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `postgresql` | `docker.io/library/postgres` | `16-alpine` | `authentik` | ❌ |
| `authentik` | `ghcr.io/goauthentik/server` | `$AUTHENTIK_TAG` | `authentik`, `traefik_backbone` | ✅ (`postgresql`) |
| `worker` | `ghcr.io/goauthentik/server` | `$AUTHENTIK_TAG` | `authentik`, `traefik_backbone` | ✅ (`postgresql`) |

---

### `monitoring` · `core_services/monitoring`
> Log aggregation and alerting. Promtail auto-discovers all Docker containers via the socket — no per-service changes needed. Grafana is SSO-integrated with Authentik.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `loki` | `grafana/loki` | `latest` | `monitoring` | ❌ |
| `promtail` | `grafana/promtail` | `latest` | `monitoring` | ✅ (`loki`) |
| `grafana` | `grafana/grafana` | `latest` | `monitoring`, `traefik_backbone` | ✅ (`loki`) |

---

### `ubiquity-console` · `core_services/networking/ubnt_console`
> Unifi Network Application and MongoDB backend for managing Ubiquiti network hardware.
> In DocoCD (`us-east-network-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `unifi-network-application` | `lscr.io/linuxserver/unifi-network-application` | `10.1.89` | *(host ports only)* | ❌ |
| `mongo` | `docker.io/mongo` | `8.2.2` | *(none defined)* | ❌ |
| `mongo-express` | `mongo-express` | `latest` | *(none defined)* | ❌ |

---

### `blocky` · `core_services/networking/blocky`
> LAN-facing DNS server with ad/tracker blocking and query logging.
> In DocoCD (`us-east-network-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `blocky` | `spx01/blocky` | `latest` | *(none defined)* | ✅ (`redis`) |
| `redis` | `redis` | `6.2-alpine` | *(none defined)* | ❌ |
| `ui` | `ghcr.io/gabeduartem/blocky-ui` | `latest` | *(none defined)* | ✅ (`blocky`) |

---

## Network Services

### `blocky-tailscale` · `network-services/blocky-tailscale`
> Tailscale-networked Blocky DNS instance. Blocky runs in the Tailscale container's network namespace so it is only reachable over the tailnet.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `tailscale` | `tailscale/tailscale` | `latest` | `internal` | ❌ |
| `redis` | `redis` | `6.2-alpine` | `internal` | ❌ |
| `blocky` | `spx01/blocky` | `latest` | `service:tailscale` (network_mode) | ✅ (`tailscale`, `redis`) |
| `blocky-ui` | `ghcr.io/gabeduartem/blocky-ui` | `latest` | `internal`, `traefik_backbone` | ✅ (`blocky`) |

---

## Web Apps

### `media_server` · `web-apps/jellyfin`
> Full media server stack including Jellyfin, Immich, *arr suite, download clients, and media management tools.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `jellyfin` | `lscr.io/linuxserver/jellyfin` | `10.11.6` | `mediaserver`, `traefik_backbone` | ❌ |
| `jellyseerr` | `seerr/seerr` | `v3.1.0` | `mediaserver`, `traefik_backbone` | ❌ |
| `immich-server` | `ghcr.io/immich-app/immich-server` | `$IMMICH_VERSION` | `mediaserver`, `traefik_backbone` | ✅ (`immich-database`, `immich-redis`) |
| `immich-machine-learning` | `ghcr.io/immich-app/immich-machine-learning` | `$IMMICH_VERSION` | `mediaserver` | ❌ |
| `immich-database` | `docker.io/tensorchord/pgvecto-rs` | `pg14-v0.2.0` | `mediaserver` | ❌ |
| `immich-redis` | `docker.io/redis` | `6.2-alpine` | `mediaserver` | ❌ |
| `sonarr` | `lscr.io/linuxserver/sonarr` | `4.0.16` | `mediaserver`, `traefik_backbone` | ❌ |
| `radarr` | `lscr.io/linuxserver/radarr` | `6.0.4` | `mediaserver`, `traefik_backbone` | ❌ |
| `lidarr` | `lscr.io/linuxserver/lidarr` | `3.1.0` | `mediaserver`, `traefik_backbone` | ❌ |
| `prowlarr` | `lscr.io/linuxserver/prowlarr` | `2.3.0` | `mediaserver`, `traefik_backbone` | ❌ |
| `bazarr` | `lscr.io/linuxserver/bazarr` | `1.5.6` | `mediaserver`, `traefik_backbone` | ❌ |
| `chaptarr` | `robertlordhood/chaptarr` | `latest` | `mediaserver`, `traefik_backbone` | ❌ |
| `rdtclient` | `rogerfar/rdtclient` | `2.0.125` | `mediaserver`, `traefik_backbone` | ❌ |
| `ariang` | `hurlenko/aria2-ariang` | `1.3.13` | `mediaserver`, `traefik_backbone` | ❌ |
| `metube` | `ghcr.io/alexta69/metube` | `2026.03.08` | `mediaserver`, `traefik_backbone` | ❌ |
| `navidrome` | `deluan/navidrome` | `0.60.3` | `mediaserver`, `traefik_backbone` | ❌ |
| `slskd` | `slskd/slskd` | `0.24.5` | `mediaserver`, `traefik_backbone` | ❌ |
| `soularr` | `mrusse08/soularr` | `latest` | `mediaserver` | ❌ |
| `rsoul` | `ghcr.io/pcs3rd/rsoul` | `release.rate-limit-test` | `mediaserver` | ❌ |
| `bliss_service` | `romancin/bliss` | `latest` | `mediaserver`, `traefik_backbone` | ❌ |
| `komga` | `ghcr.io/gotson/komga` | `1.24.3` | `mediaserver`, `traefik_backbone` | ❌ |
| `tinshop` | `ghcr.io/ajmandourah/tinshop-ng` | `v0.5.3` | `mediaserver`, `traefik_backbone` | ❌ |
| `calibre` | `lscr.io/linuxserver/calibre` | `latest` | `traefik_backbone` | ❌ |
| `tvheadend` | `ghcr.io/linuxserver/tvheadend` | `version-7c4011de` | `host` (network_mode) | ❌ |
| `tdarr` | `ghcr.io/haveagitgat/tdarr` | `latest` | `bridge` (network_mode) | ❌ |
| `ersatztv` | `ghcr.io/ersatztv/ersatztv` | `latest` | `mediaserver` | ❌ |
| `flaresolverr` | `ghcr.io/flaresolverr/flaresolverr` | `v3.4.6` | `mediaserver` | ❌ |

---

### `seafile` · `web-apps/seafile`
> Self-hosted file sync and share with WebDAV support.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `db` | `mariadb` | `10.11` | `internal` | ❌ |
| `memcached` | `memcached` | `1.6.18` | `internal` | ❌ |
| `seafile` | `seafileltd/seafile-mc` | `11.0-latest` | `internal`, `traefik_backbone` (`backbone`) | ✅ (`db`, `memcached`) |

---

### `affine` · `web-apps/affine`
> Collaborative knowledge base / whiteboard workspace.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `affine` | `ghcr.io/toeverything/affine` | `$AFFINE_REVISION` | `internal`, `traefik_backbone` | ❌ |
| `affine_migration` | `ghcr.io/toeverything/affine` | `$AFFINE_REVISION` | `internal` | ❌ |
| `redis` | `redis` | `latest` | `internal` | ❌ |
| `postgres` | `pgvector/pgvector` | `pg16` | `internal` | ❌ |

---

### `kiwix` · `web-apps/kiwix`
> Offline Wikipedia, Gutenberg, iFixit, CDC, and other ZIM archive server.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `kiwix-server` | `ghcr.io/kiwix/kiwix-serve` | `latest` | `traefik_backbone` | ❌ |

---

### `meshtastic` · `web-apps/meshtastic`
> Meshtastic daemon and mesh bot for LoRa radio mesh networking.
> In DocoCD (`us-east-stickpile-prod`): ✅

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `meshing-around` | `ghcr.io/spudgunman/meshing-around` | `main` | `mesh-internal` | ❌ |
| `meshtasticd` | `meshtastic/meshtasticd` | `2.7.15.d18f3f7-beta-alpine` | `mesh-internal` | ❌ |

---

### `mixpost` · `web-apps/mixpost`
> Social media scheduling and management. ⚠️ Currently commented out in DocoCD.
> In DocoCD (`us-east-stickpile-prod`): ❌ *(commented out)*

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `mixpost` | `inovector/mixpost` | `latest` | `internal`, `traefik_backbone` | ✅ (`mysql`, `redis`) |
| `mysql` | `mysql/mysql-server` | `8.0` | `internal` | ❌ |
| `redis` | `redis` | `latest` | `internal` | ❌ |

---

### `wordpress` · `web-apps/wordpress`
> WordPress site (raymonddean.me). Not present in either DocoCD file.
> In DocoCD: ❌

| Container | Image | Version | Networks | depends_on |
|---|---|---|---|---|
| `wpdb` | `mariadb` | `10.6.4-focal` | `internal` | ❌ |
| `wordpress` | `wordpress` | `latest` | `internal`, `traefik_backbone` | ❌ |

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
