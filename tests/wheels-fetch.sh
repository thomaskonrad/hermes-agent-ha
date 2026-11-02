#!/bin/sh
# Download the pinned pytest wheels used by run-in-image.sh into .wheels/.
# Pinned so the in-image test runner is reproducible. The wheels are only used
# to run tests; they are never installed into the app image.
set -eu
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$REPO/.wheels"
rm -rf "$OUT" && mkdir -p "$OUT"
"$REPO/.venv/bin/python" -m pip download -q --only-binary=:all: -d "$OUT" "pytest==8.4.2"
ls "$OUT"
