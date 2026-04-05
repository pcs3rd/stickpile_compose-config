#!/bin/sh
# Write the bouncer key from env to a tmpfs file for the plugin to read
echo -n "$BOUNCER_API_KEY" > /run/secrets/bouncer_api_key
exec /entrypoint.sh "$@"