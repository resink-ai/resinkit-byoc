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
    # if current branch is release branch, then pull
    if git -C "$ROOT_DIR" branch --show-current | grep -q "$RESINKIT_BYOC_RELEASE_BRANCH"; then
        git -C "$ROOT_DIR" pull --rebase
    else
        # checkout to release branch
        git -C "$ROOT_DIR" branch -D "$RESINKIT_BYOC_RELEASE_BRANCH" || true
        git -C "$ROOT_DIR" fetch origin "$RESINKIT_BYOC_RELEASE_BRANCH"
        git -C "$ROOT_DIR" checkout -b "$RESINKIT_BYOC_RELEASE_BRANCH" origin/"$RESINKIT_BYOC_RELEASE_BRANCH"
    fi
fi

cd "$ROOT_DIR"
