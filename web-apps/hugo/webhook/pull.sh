#!/bin/sh
git config --global --add safe.directory /src
set -e
git -C /src pull
chown 1000:1000 -R /src