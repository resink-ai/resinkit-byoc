#!/bin/bash
# shellcheck disable=SC1091,SC2046

: "${ROOT_DIR:?}" "${RESINKIT_BYOC_RELEASE_BRANCH:?}"

set -eo pipefail

if [ ! -f "/opt/uv/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/opt/uv" sh
fi

if [ ! -d "$ROOT_DIR" ]; then
    # clone resinkit-byoc repo
    git clone --branch "$RESINKIT_BYOC_RELEASE_BRANCH" https://github.com/resink-ai/resinkit-byoc.git "$ROOT_DIR"
else
    echo "[RESINKIT] resinkit-byoc repo already exists, skip cloning or pulling to avoid overwriting local changes"
    true
fi

# install git lfs if not installed
if ! command -v git-lfs &> /dev/null; then
    apt-get update
    apt-get install git-lfs -y --no-install-recommends
fi

# install git lfs
git lfs install || true
