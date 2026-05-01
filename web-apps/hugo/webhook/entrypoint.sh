#!/bin/sh
set -e

# Seed repo on first start
if [ -z "$GIT_REPO_URL" ]; then
  echo "GIT_REPO_URL is not set — skipping clone"
elif [ ! -d /src/.git ]; then
  echo "Cloning $GIT_REPO_URL into /src..."
  git clone "$GIT_REPO_URL" /src
  echo "Clone complete."
else
  echo "Repository already present, skipping clone."
fi

# Ensure pull.sh is executable (volume mounts don't preserve build-time chmod)
chmod +x /hooks/pull.sh

# Generate hooks.json with the secret injected at runtime
cat > /tmp/hooks.json << EOF
[
  {
    "id": "deploy",
    "execute-command": "/hooks/pull.sh",
    "command-working-directory": "/src",
    "response-message": "Deploying latest changes...",
    "trigger-rule": {
      "match": {
        "type": "payload-hmac-sha256",
        "secret": "$WEBHOOK_SECRET",
        "parameter": {
          "source": "header",
          "name": "X-Hub-Signature-256"
        }
      }
    }
  }
]
EOF

exec webhook -hooks /tmp/hooks.json -verbose -port 9000