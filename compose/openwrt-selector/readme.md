## OpenWrt Firmware Selector + ASU
----
Self-hosted [OpenWrt Firmware Selector](https://github.com/openwrt/firmware-selector-openwrt-org) backed by its own
[ASU](https://github.com/openwrt/asu) (Attended SysUpgrade) build server, so custom images (extra packages, first-boot
script) are built here instead of on sysupgrade.openwrt.org.

- URL: https://firmware.stickpile.net, gated by Authentik forward-auth (`middlewares-authentik@file`, same as kiwix).
- One hostname, three routes: `/` is the selector (nginx), `/api/v1` and `/store` go to the ASU API. Same origin, so no CORS and the Authentik cookie covers the API calls.
- Stock images and the version list still come from `downloads.openwrt.org`; only custom builds hit our ASU.
- No secrets, no NFS, no host ports. All volumes are local.

### Before first deploy
1. DNS: `firmware.stickpile.net` -> this host (same as the other Traefik hosts).
2. Authentik: create a **Proxy Provider** (forward auth, single application) for `https://firmware.stickpile.net`, an application for it, and add it to the embedded outpost. Restrict access with a group policy.
3. Disk: budget roughly 50-200 GB. The `podman_storage` volume caches one ImageBuilder image (about 1 GB) per target you build for, and `asu_public` keeps finished builds.

### How it fits together
- `selector`: stock `nginx:alpine`. On start it downloads the pinned selector release (`SELECTOR_VERSION`, default `v5.1.0`) from GitHub, copies `www/` into the web root and overlays `config.js` from this folder. Needs outbound HTTPS to github.com at container start. To upgrade, change `SELECTOR_VERSION` and redeploy.
- `config.js`: `asu_url` must equal the public hostname. `asu_extra_packages` is added to every custom build (commented example includes `tailscale` and `openwisp-config`).
- `asu` / `worker` / `redis`: upstream ASU. Redis must be **redis-stack** (ASU uses the TimeSeries module for stats).
- `podman`: ASU runs ImageBuilder in containers through a **Podman** API socket (podman-py; a Docker socket does not work). A privileged `quay.io/podman/stable` sidecar provides the socket on a shared volume and creates the isolated `asu-build` network. The worker symlinks the socket to `/var/podman.sock`, where ASU looks for it.
- `ALLOW_DEFAULTS=true` enables the selector's first-boot script (uci-defaults) field, e.g. to point a new device at OpenWISP. It runs inside the image build, and the site is behind Authentik.

### Things to know
- **The `podman` service is `privileged`** and runs containers inside a container. If nested overlay storage misbehaves on this host, the alternative is a host Podman socket: enable `virtualisation.podman` plus `podman.socket` in the nix-config, create the `asu-build` network there, bind that socket into `worker` at `/var/podman.sock`, and delete the `podman` service and its volumes.
- Builds are **not signed** (no `BUILD_KEY`). Signing needs the key mounted at the same path in both `worker` and `podman`. Flashing from the web UI works without it.
- `ASU_VERSION` and `PODMAN_VERSION` default to `latest`; pin them if an upstream change breaks something.
- The apk-based releases (25.12 and snapshots) build fine; ASU handles the package manager difference itself.

### Troubleshooting
- Selector loads but "Request Build" fails: check the `worker` logs (set `LOG_LEVEL: DEBUG` in `compose.yaml` to see the Podman calls), and make sure `podman` is healthy.
- Build fails with a network error: confirm `asu-build` exists (`docker exec <podman> podman network ls`) and that the sidecar has internet access.
- 302/redirect loops on `/api/v1`: the Authentik provider does not cover the whole hostname.
- Blank page or no versions: the selector could not fetch `https://downloads.openwrt.org/.versions.json` (check the browser console) or the tarball download failed at start (check the `selector` logs).
