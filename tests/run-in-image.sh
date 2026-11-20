#!/bin/sh
# Run the in-image test suite (seeder, real python-dotenv) against an image.
#
# Usage: tests/run-in-image.sh <image-tag> [platform]
#   image-tag  e.g. hermes-agent-ha:m0-arm64 (must be built from this repo)
#   platform   e.g. linux/arm64 (default: the host platform)
#
# Colima only shares $HOME into the VM, so the repo is staged under $HOME.
# pytest is installed from the wheels in tests/wheels-fetch.sh into /tmp/pt
# inside the container; the image's own python-dotenv is the one under test.
set -eu

IMAGE="${1:?usage: run-in-image.sh <image-tag> [platform]}"
PLATFORM="${2:-}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$HOME/hermes-ha-testrun"

rm -rf "$STAGE" && mkdir -p "$STAGE"
cp -R "$REPO/tests" "$STAGE/"
cp -R "$REPO/hermes_agent" "$STAGE/"
cp "$REPO/repository.yaml" "$STAGE/"
if [ -d "$REPO/.wheels" ]; then
    cp -R "$REPO/.wheels" "$STAGE/wheels"
else
    echo "missing $REPO/.wheels: run tests/wheels-fetch.sh first" >&2
    exit 1
fi

cat > "$STAGE/run.sh" <<'EOF'
set -e
cd /w
/opt/hermes/.venv/bin/python -c "import zipfile,glob,os; t='/tmp/pt'; os.makedirs(t,exist_ok=True); [zipfile.ZipFile(w).extractall(t) for w in glob.glob('/w/wheels/*.whl')]"
PYTHONPATH=/tmp/pt:/w /opt/hermes/.venv/bin/python -m pytest tests/test_options_seed.py -q -p no:cacheprovider
EOF

if [ -n "$PLATFORM" ]; then
    docker run --rm --platform "$PLATFORM" -v "$STAGE:/w" --entrypoint sh "$IMAGE" /w/run.sh
else
    docker run --rm -v "$STAGE:/w" --entrypoint sh "$IMAGE" /w/run.sh
fi
