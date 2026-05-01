#!/bin/sh
git config --global --add safe.directory /src
set -e
git -C /src pull
