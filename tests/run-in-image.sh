#!/bin/sh
# Run the in-image test suite (seeder, real python-dotenv) against an image.
#
# Usage: tests/run-in-image.sh <image-tag> [platform]
#   image-tag  e.g. hermes-agent-ha:dev-arm64 (must be built from this repo)
#   platform   e.g. linux/arm64 (default: the host platform)
#
# Colima only shares $HOME into the VM, so the repo is staged under $HOME.
# pytest (pinned) is downloaded here and installed into /tmp/pt inside the
# container. The image's own python-dotenv is the one under test. The wheels
# are never installed into the app image.
set -eu

IMAGE="${1:?usage: run-in-image.sh <image-tag> [platform]}"
PLATFORM="${2:-}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$HOME/hermes-ha-testrun"

rm -rf "$STAGE" && mkdir -p "$STAGE/wheels"
cp -R "$REPO/tests" "$REPO/hermes_agent" "$REPO/repository.yaml" "$STAGE/"
python3 -m pip download -q --only-binary=:all: -d "$STAGE/wheels" "pytest==8.4.2"

cat > "$STAGE/run.sh" <<'EOF'
set -e
cd /w
mkdir -p /tmp/pt
/opt/hermes/.venv/bin/python -c "import zipfile,glob; [zipfile.ZipFile(w).extractall('/tmp/pt') for w in glob.glob('/w/wheels/*.whl')]"
PYTHONPATH=/tmp/pt:/w /opt/hermes/.venv/bin/python -m pytest tests/test_options_seed.py -q -p no:cacheprovider
EOF

if [ -n "$PLATFORM" ]; then
    docker run --rm --platform "$PLATFORM" -v "$STAGE:/w" --entrypoint sh "$IMAGE" /w/run.sh
else
    docker run --rm -v "$STAGE:/w" --entrypoint sh "$IMAGE" /w/run.sh
fi
