# Migration Guide: Bind Mounts → NFS + Local Named Volumes

This guide covers migrating each stack from the old bind-mount layout (based on `$persist_data_home`) to the current named volume setup — NFS volumes for most data, local volumes for databases.

---

## Prerequisites

Before migrating any stack:

1. **NFS server is reachable** and the share paths exist (or will be created on first write).
2. **Node labels are applied** — see the [README](../README.md#swarm-node-labels) for the full list. Each stack section below calls out which labels it needs.
3. **All stacks are stopped** before you begin moving data for that stack.

Set a shell variable for your old data root to make the commands below copy-pasteable:

```bash
export OLD_BASE=/your/old/persist_data_home
export NFS_SHARE=/mnt/your/nfs/share   # or the NFS server path, e.g. /tank/docker
```

---

## Patterns

### NFS volume migration (file data)

For any NFS-backed volume, the migration is an rsync from the old bind-mount directory to the NFS share path:

```bash
rsync -av --progress <old_path>/ <nfs_path>/
```

The trailing `/` on the source is important — it copies the contents, not the directory itself.

### Local volume migration (databases)

Databases need different handling depending on the engine. See the per-database sections below. The general rule is: **stop the container first, never copy a live database**.

---

## Shared Volumes (migrate once, used by multiple stacks)

These should be migrated before deploying any stack that uses them.

| Volume | NFS path | Old bind mount |
|---|---|---|
| `downloads` | `$NFS_SHARE/downloads` | `$OLD_BASE/downloads` (or `$downloads_home`) |
| `media` | `$NFS_SHARE/media` | `$OLD_BASE/media` (or `$media_mount`) |
| `games_data` | `$NFS_SHARE/media/2111/games` | `$OLD_BASE/media/2111/games` |

```bash
rsync -av --progress $OLD_BASE/downloads/  $NFS_SHARE/downloads/
rsync -av --progress $OLD_BASE/media/      $NFS_SHARE/media/
```

---

## Stack: `core_services/traefik`

**Node label required:** none (runs on Swarm manager)

### SQLite — CrowdSec (`crowdsec_db`, local volume)

CrowdSec's database is SQLite at `/var/lib/crowdsec/data` inside the container.

```bash
# 1. Stop the stack
docker stack rm traefik  # or: docker compose down

# 2. Copy the database files into the new local volume
#    The stack name prefix will be 'traefik' — adjust if different
docker run --rm \
  -v $OLD_BASE/crowdsec/data:/source:ro \
  -v traefik_crowdsec_db:/target \
  alpine sh -c "cp -a /source/. /target/"

# 3. Migrate NFS volumes (see table below), then deploy
```

### NFS volumes

| Volume | NFS path | Old bind mount |
|---|---|---|
| `crowdsec_config` | `$NFS_SHARE/appdata/crowdsec/config` | `$OLD_BASE/crowdsec/config` |
| `crowdsec_logs` | `$NFS_SHARE/appdata/crowdsec/log` | `$OLD_BASE/crowdsec/log` |
| `geoip` | `$NFS_SHARE/appdata/geoip` | `$OLD_BASE/geoip` |
| `letsencrypt_data` | `$NFS_SHARE/appdata/letsencrypt` | `$OLD_BASE/letsencrypt` |
| `proxy-logs` | `$NFS_SHARE/appdata/traefik/logs` | `$OLD_BASE/traefik/logs` |

```bash
rsync -av --progress $OLD_BASE/crowdsec/config/  $NFS_SHARE/appdata/crowdsec/config/
rsync -av --progress $OLD_BASE/crowdsec/log/     $NFS_SHARE/appdata/crowdsec/log/
rsync -av --progress $OLD_BASE/geoip/            $NFS_SHARE/appdata/geoip/
rsync -av --progress $OLD_BASE/letsencrypt/      $NFS_SHARE/appdata/letsencrypt/
rsync -av --progress $OLD_BASE/traefik/logs/     $NFS_SHARE/appdata/traefik/logs/
```

---

## Stack: `core_services/authentik`

**Node label required:** `role=authentik` on the node that will hold the PostgreSQL volume.

### PostgreSQL (`postgresql_data`, local volume)

```bash
# 1. Dump the database while still running
docker exec authentik_postgresql_1 pg_dumpall -U postgres > authentik_backup.sql

# 2. Stop the stack
docker stack rm authentik  # or: docker compose down

# 3. Start a temporary PostgreSQL container with the new local volume
docker run -d --name pg_restore \
  -v authentik_postgresql_data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=temp \
  postgres:16-alpine

# 4. Wait for it to be ready
sleep 5 && docker exec pg_restore pg_isready

# 5. Restore the dump
docker exec -i pg_restore psql -U postgres < authentik_backup.sql

# 6. Clean up
docker rm -f pg_restore
```

### NFS volumes

| Volume | NFS path | Old bind mount |
|---|---|---|
| `authentik_media` | `$NFS_SHARE/appdata/authentik/media` | `$OLD_BASE/authentik/media` |
| `authentik_templates` | `$NFS_SHARE/appdata/authentik/custom-templates` | `$OLD_BASE/authentik/custom-templates` |
| `authentik_certs` | `$NFS_SHARE/appdata/authentik/certs` | `$OLD_BASE/authentik/certs` |
| `authentik_blueprints` | `$NFS_SHARE/appdata/authentik/blueprints` | `$OLD_BASE/authentik/blueprints` |

```bash
rsync -av --progress $OLD_BASE/authentik/media/             $NFS_SHARE/appdata/authentik/media/
rsync -av --progress $OLD_BASE/authentik/custom-templates/  $NFS_SHARE/appdata/authentik/custom-templates/
rsync -av --progress $OLD_BASE/authentik/certs/             $NFS_SHARE/appdata/authentik/certs/
rsync -av --progress $OLD_BASE/authentik/blueprints/        $NFS_SHARE/appdata/authentik/blueprints/
```

---

## Stack: `core_services/monitoring`

**Node label required:** none.

All volumes are NFS — no database migration needed.

### NFS volumes

| Volume | NFS path | Old bind mount |
|---|---|---|
| `alloy_data` | `$NFS_SHARE/appdata/alloy` | `$OLD_BASE/alloy` |
| `grafana_data` | `$NFS_SHARE/appdata/grafana` | `$OLD_BASE/grafana` |
| `loki_data` | `$NFS_SHARE/appdata/loki` | `$OLD_BASE/loki` |

```bash
rsync -av --progress $OLD_BASE/alloy/    $NFS_SHARE/appdata/alloy/
rsync -av --progress $OLD_BASE/grafana/  $NFS_SHARE/appdata/grafana/
rsync -av --progress $OLD_BASE/loki/     $NFS_SHARE/appdata/loki/
```

---

## Stack: `web-apps/seafile`

**Node label required:** `role=seafile` on the node that will hold the MariaDB volume.

### MariaDB (`seafile_db`, local volume)

```bash
# 1. Dump the database while still running
docker exec seafile_db_1 mysqldump \
  -u root -p"${MARIADB_ROOT_PASSWORD}" \
  --all-databases \
  --single-transaction \
  > seafile_backup.sql

# 2. Stop the stack
docker stack rm seafile  # or: docker compose down

# 3. Start a temporary MariaDB container with the new local volume
docker run -d --name mariadb_restore \
  -v seafile_seafile_db:/var/lib/mysql \
  -e MARIADB_ROOT_PASSWORD=your_root_password \
  mariadb:10.11

# 4. Wait for it to be ready
docker exec mariadb_restore mysqladmin -u root -p"your_root_password" ping --wait

# 5. Restore the dump
docker exec -i mariadb_restore mysql -u root -p"your_root_password" < seafile_backup.sql

# 6. Clean up
docker rm -f mariadb_restore
```

### NFS volumes

| Volume | NFS path | Old bind mount |
|---|---|---|
| `seafile_data` | `$NFS_SHARE/appdata/seafile-data` | `$OLD_BASE/seafile/data` |

```bash
rsync -av --progress $OLD_BASE/seafile/data/  $NFS_SHARE/appdata/seafile-data/
```

---

## Stack: `web-apps/jellyfin`

**Node labels required:** `role=media` and `intel.gpu=true` on the media node.

### SQLite — Jellyfin (`jellyfin_db`, local volume)

Jellyfin stores its SQLite databases under `/config/data` inside the container. The rest of `/config` goes to the NFS `jellyfin_data` volume; only `/config/data` is local.

```bash
# 1. Stop the stack
docker stack rm media_server  # or: docker compose down

# 2. Migrate /config (everything except /config/data) to NFS
rsync -av --progress --exclude='data/' \
  $OLD_BASE/jellyfin/  $NFS_SHARE/appdata/jellyfin/

# 3. Copy /config/data into the local volume
docker run --rm \
  -v $OLD_BASE/jellyfin/data:/source:ro \
  -v media_server_jellyfin_db:/target \
  alpine sh -c "cp -a /source/. /target/"
```

### NFS volumes

| Volume | NFS path | Old bind mount |
|---|---|---|
| `jellyfin_data` | `$NFS_SHARE/appdata/jellyfin` | `$OLD_BASE/jellyfin` (excl. `/data`) |
| `aria2_data` | `$NFS_SHARE/appdata/aria2` | `$OLD_BASE/aria2` |
| `bazarr_data` | `$NFS_SHARE/appdata/bazaar` | `$OLD_BASE/bazarr` |
| `bliss_data` | `$NFS_SHARE/appdata/bliss` | `$OLD_BASE/bliss` |
| `calibre_data` | `$NFS_SHARE/appdata/calibre/config` | `$OLD_BASE/calibre/config` |
| `chaptarr_data` | `$NFS_SHARE/appdata/chaptarr` | `$OLD_BASE/chaptarr` |
| `cleanuparr_data` | `$NFS_SHARE/appdata/cleanuparr` | `$OLD_BASE/cleanuparr` |
| `ersatztv_data` | `$NFS_SHARE/appdata/ErsatzTV` | `$OLD_BASE/ErsatzTV` |
| `jellyseerr_data` | `$NFS_SHARE/appdata/jellyseerr` | `$OLD_BASE/jellyseerr` |
| `komga_config` | `$NFS_SHARE/appdata/komga/config` | `$OLD_BASE/komga/config` |
| `komga_data` | `$NFS_SHARE/appdata/komga/data` | `$OLD_BASE/komga/data` |
| `lidarr_data` | `$NFS_SHARE/appdata/lidarr` | `$OLD_BASE/lidarr` |
| `lidarr_custom_init` | `$NFS_SHARE/appdata/lidarr-overlay/custom-cont-init.d` | `$OLD_BASE/lidarr-overlay/custom-cont-init.d` |
| `lidarr_custom_services` | `$NFS_SHARE/appdata/lidarr-overlay/custom-services.d` | `$OLD_BASE/lidarr-overlay/custom-services.d` |
| `metube_downloads` | `$NFS_SHARE/downloads/yt-dlp` | `$OLD_BASE/downloads/yt-dlp` |
| `navidrome_data` | `$NFS_SHARE/appdata/navidrome` | `$OLD_BASE/navidrome` |
| `prowlarr_data` | `$NFS_SHARE/appdata/prowlarr` | `$OLD_BASE/prowlarr` |
| `radarr_data` | `$NFS_SHARE/appdata/radarr` | `$OLD_BASE/radarr` |
| `rdtclient_data` | `$NFS_SHARE/appdata/rdt-client` | `$OLD_BASE/rdt-client` |
| `rsoul_data` | `$NFS_SHARE/appdata/rsoul` | `$OLD_BASE/rsoul` |
| `slskd_data` | `$NFS_SHARE/appdata/slskd` | `$OLD_BASE/slskd` |
| `sonarr_data` | `$NFS_SHARE/appdata/sonarr` | `$OLD_BASE/sonarr` |
| `soularr_data` | `$NFS_SHARE/appdata/soularr` | `$OLD_BASE/soularr` |
| `tdarr_data` | `$NFS_SHARE/appdata/tdarr` | `$OLD_BASE/tdarr` |

```bash
rsync -av --progress $OLD_BASE/aria2/          $NFS_SHARE/appdata/aria2/
rsync -av --progress $OLD_BASE/bazarr/         $NFS_SHARE/appdata/bazaar/
rsync -av --progress $OLD_BASE/bliss/          $NFS_SHARE/appdata/bliss/
rsync -av --progress $OLD_BASE/calibre/config/ $NFS_SHARE/appdata/calibre/config/
rsync -av --progress $OLD_BASE/chaptarr/       $NFS_SHARE/appdata/chaptarr/
rsync -av --progress $OLD_BASE/cleanuparr/     $NFS_SHARE/appdata/cleanuparr/
rsync -av --progress $OLD_BASE/ErsatzTV/       $NFS_SHARE/appdata/ErsatzTV/
rsync -av --progress $OLD_BASE/jellyseerr/     $NFS_SHARE/appdata/jellyseerr/
rsync -av --progress $OLD_BASE/komga/config/   $NFS_SHARE/appdata/komga/config/
rsync -av --progress $OLD_BASE/komga/data/     $NFS_SHARE/appdata/komga/data/
rsync -av --progress $OLD_BASE/lidarr/         $NFS_SHARE/appdata/lidarr/
rsync -av --progress $OLD_BASE/lidarr-overlay/custom-cont-init.d/   $NFS_SHARE/appdata/lidarr-overlay/custom-cont-init.d/
rsync -av --progress $OLD_BASE/lidarr-overlay/custom-services.d/    $NFS_SHARE/appdata/lidarr-overlay/custom-services.d/
rsync -av --progress $OLD_BASE/downloads/yt-dlp/  $NFS_SHARE/downloads/yt-dlp/
rsync -av --progress $OLD_BASE/navidrome/      $NFS_SHARE/appdata/navidrome/
rsync -av --progress $OLD_BASE/prowlarr/       $NFS_SHARE/appdata/prowlarr/
rsync -av --progress $OLD_BASE/radarr/         $NFS_SHARE/appdata/radarr/
rsync -av --progress $OLD_BASE/rdt-client/     $NFS_SHARE/appdata/rdt-client/
rsync -av --progress $OLD_BASE/rsoul/          $NFS_SHARE/appdata/rsoul/
rsync -av --progress $OLD_BASE/slskd/          $NFS_SHARE/appdata/slskd/
rsync -av --progress $OLD_BASE/sonarr/         $NFS_SHARE/appdata/sonarr/
rsync -av --progress $OLD_BASE/soularr/        $NFS_SHARE/appdata/soularr/
rsync -av --progress $OLD_BASE/tdarr/          $NFS_SHARE/appdata/tdarr/
rsync -av --progress $OLD_BASE/tvheadend/data/ $NFS_SHARE/appdata/tvheadend/data/
```

---

## Stack: `network-services/blocky-tailscale`

**Node label required:** none.

All volumes are NFS — no database migration needed.

### NFS volumes

| Volume | NFS path | Old bind mount |
|---|---|---|
| `qlogs` | `$NFS_SHARE/appdata/blocky/querylog` | `$OLD_BASE/blocky/querylog` |
| `redis_data` | `$NFS_SHARE/appdata/redis-state` | `$OLD_BASE/redis` |
| `tailscale_data` | `$NFS_SHARE/appdata/tailscale/state` | `$OLD_BASE/tailscale/state` |

```bash
rsync -av --progress $OLD_BASE/blocky/querylog/  $NFS_SHARE/appdata/blocky/querylog/
rsync -av --progress $OLD_BASE/redis/            $NFS_SHARE/appdata/redis-state/
rsync -av --progress $OLD_BASE/tailscale/state/  $NFS_SHARE/appdata/tailscale/state/
```

---

## Stack: `web-apps/kiwix`

**Node label required:** none.

Kiwix only stores `.zim` files — no config state to migrate. Just copy your `.zim` files to the NFS path and they'll be picked up on first deploy.

| Volume | NFS path |
|---|---|
| `kiwix_data` | `$NFS_SHARE/appdata/kiwix-server/data` |

```bash
rsync -av --progress $OLD_BASE/kiwix/data/  $NFS_SHARE/appdata/kiwix-server/data/
```

---

## Verifying a volume after migration

Before deploying, you can spin up a quick alpine container to confirm the data landed correctly:

```bash
docker run --rm \
  -v <stack>_<volume>:/data \
  alpine ls -lah /data
```

For databases, start the service and check the application logs before considering the migration complete.
