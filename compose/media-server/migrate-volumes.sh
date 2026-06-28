#!/bin/bash
# One-time migration: recreate NFS-backed volumes as local Docker volumes,
# copying existing data in the process. Also creates new local volumes for
# bazarr_db, jellyseerr_db, and slskd_db from their respective NFS subdirs.
#
# Run on the container host as a user with Docker access:
#   bash migrate-volumes.sh

set -euo pipefail

PROJECT="media_server"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Stop a service by project + service name using container labels (no compose file needed)
stop_service() {
    local svc="$1"
    local cid
    cid=$(docker ps -q \
        --filter "label=com.docker.compose.project=${PROJECT}" \
        --filter "label=com.docker.compose.service=${svc}")
    if [ -n "$cid" ]; then
        echo "  Stopping and removing ${svc} (${cid})..."
        docker stop "$cid" > /dev/null
        docker rm "$cid" > /dev/null
    else
        # Container may already be stopped but not removed
        local stopped_cid
        stopped_cid=$(docker ps -aq \
            --filter "label=com.docker.compose.project=${PROJECT}" \
            --filter "label=com.docker.compose.service=${svc}")
        if [ -n "$stopped_cid" ]; then
            echo "  ${svc} already stopped — removing container (${stopped_cid})..."
            docker rm "$stopped_cid" > /dev/null
        else
            echo "  ${svc} has no container — skipping."
        fi
    fi
}

# Recreate an NFS-backed named volume as a plain local volume, preserving data.
# Uses an intermediate temp volume so we never touch the NFS server directly.
# Skips the volume if it is already a plain local volume.
migrate_nfs_to_local() {
    local short_name="$1"
    local vol="${PROJECT}_${short_name}"
    local tmp="${vol}__mig"

    echo ""
    echo "=== ${vol}: NFS → local ==="

    if ! docker volume inspect "$vol" --format '{{.Options.type}}' 2>/dev/null | grep -q nfs; then
        echo "  Already a local volume — skipping."
        return
    fi

    docker volume create "$tmp" > /dev/null
    echo "  Copying from NFS volume..."
    docker run --rm \
        -v "${vol}:/src:ro" \
        -v "${tmp}:/dst" \
        alpine sh -c 'cp -a /src/. /dst/'

    echo "  Removing NFS volume..."
    docker volume rm "$vol" > /dev/null

    echo "  Creating local volume..."
    docker volume create "$vol" > /dev/null

    echo "  Restoring data..."
    docker run --rm \
        -v "${tmp}:/src:ro" \
        -v "${vol}:/dst" \
        alpine sh -c 'cp -a /src/. /dst/'

    docker volume rm "$tmp" > /dev/null
    echo "  Done."
}

# Create a new local volume populated from a subdirectory of an existing NFS volume.
# Skips if the volume already exists.
create_from_subdir() {
    local new_short="$1"
    local parent_short="$2"
    local subdir="$3"
    local new_vol="${PROJECT}_${new_short}"
    local parent_vol="${PROJECT}_${parent_short}"

    echo ""
    echo "=== Creating ${new_vol} from ${parent_vol}/${subdir} ==="

    if docker volume inspect "$new_vol" > /dev/null 2>&1; then
        echo "  Volume already exists — skipping."
        return
    fi

    docker volume create "$new_vol" > /dev/null
    docker run --rm \
        -v "${parent_vol}:/src:ro" \
        -v "${new_vol}:/dst" \
        alpine sh -c "
            if [ -d /src/${subdir} ] && [ \"\$(ls -A /src/${subdir} 2>/dev/null)\" ]; then
                cp -a /src/${subdir}/. /dst/
                echo '  Copied existing data.'
            else
                echo '  ${subdir}/ is empty or absent — volume created empty (OK for fresh installs).'
            fi
        "
    echo "  Done."
}

# ---------------------------------------------------------------------------
# Clean up any leftover temp volumes from a previous failed run
# ---------------------------------------------------------------------------

leftover=$(docker volume ls -q --filter name=__mig)
if [ -n "$leftover" ]; then
    echo "Cleaning up leftover temp volumes from previous run..."
    echo "$leftover" | xargs docker volume rm
    echo ""
fi

# ---------------------------------------------------------------------------
# Determine what actually needs to run, then stop only those services
# ---------------------------------------------------------------------------

needs_migrate=()
for vol in radarr_data sonarr_data lidarr_data prowlarr_data chaptarr_data rdtclient_data; do
    if docker volume inspect "${PROJECT}_${vol}" --format '{{.Options.type}}' 2>/dev/null | grep -q nfs; then
        needs_migrate+=("$vol")
    fi
done

needs_create=()
for spec in "bazarr_db:bazarr_data:db" "jellyseerr_db:jellyseerr_data:db" "slskd_db:slskd_data:data"; do
    new_vol="${spec%%:*}"
    if ! docker volume inspect "${PROJECT}_${new_vol}" > /dev/null 2>&1; then
        needs_create+=("$spec")
    fi
done

if [ ${#needs_migrate[@]} -eq 0 ] && [ ${#needs_create[@]} -eq 0 ]; then
    echo "Nothing to do — all volumes are already migrated."
    exit 0
fi

echo "Will migrate: ${needs_migrate[*]:-none}"
echo "Will create:  $(echo "${needs_create[*]:-none}" | tr ':' '/' | sed 's/ /  /g')"
echo ""

# Map volume names to service names for targeted stops
declare -A VOL_TO_SVC=(
    [radarr_data]=radarr
    [sonarr_data]=sonarr
    [lidarr_data]=lidarr
    [prowlarr_data]=prowlarr
    [chaptarr_data]=chaptarr
    [rdtclient_data]=rdtclient
    [bazarr_db]=bazarr
    [jellyseerr_db]=jellyseerr
    [slskd_db]=slskd
)

svcs_to_stop=()
for vol in "${needs_migrate[@]}"; do
    svcs_to_stop+=("${VOL_TO_SVC[$vol]}")
done
for spec in "${needs_create[@]}"; do
    new_vol="${spec%%:*}"
    svcs_to_stop+=("${VOL_TO_SVC[$new_vol]}")
done

echo "Stopping services: ${svcs_to_stop[*]}"
for svc in "${svcs_to_stop[@]}"; do
    stop_service "$svc"
done

# ---------------------------------------------------------------------------
# Migrate full NFS volumes → local
# ---------------------------------------------------------------------------

for vol in "${needs_migrate[@]}"; do
    migrate_nfs_to_local "$vol"
done

# ---------------------------------------------------------------------------
# Create new local subdirectory volumes
# ---------------------------------------------------------------------------

for spec in "${needs_create[@]}"; do
    IFS=: read -r new_vol parent_vol subdir <<< "$spec"
    create_from_subdir "$new_vol" "$parent_vol" "$subdir"
done

# ---------------------------------------------------------------------------

echo ""
echo "All migrations complete."
echo "Services are stopped. Start them via doco-cd push or trigger a redeploy."
