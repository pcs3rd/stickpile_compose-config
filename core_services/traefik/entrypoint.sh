#!/bin/sh
# Write the bouncer key from env to a tmpfs file for the plugin to read
echo -n "$BOUNCER_KEY_TRAEFIK" > /run/secrets/bouncer_api_key
exec /entrypoint.sh "$@"