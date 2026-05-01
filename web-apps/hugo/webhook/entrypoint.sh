#!/bin/sh
set -e

if [ -z "$GIT_REPO_URL" ]; then
  echo "GIT_REPO_URL is not set — skipping clone"
elif [ ! -d /src/.git ]; then
  echo "Cloning $GIT_REPO_URL into /src..."
  git clone "$GIT_REPO_URL" /src
  echo "Clone complete."
else
  echo "Repository already present, skipping clone."
fi

exec webhook "$@"
