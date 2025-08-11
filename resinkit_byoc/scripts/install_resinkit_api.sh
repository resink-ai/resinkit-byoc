#!/bin/bash

set -eo pipefail
: "${ROOT_DIR:?}"


function install_resinkit_api() {
    # Check if resinkit-api is already installed
    if [ -d "/opt/resinkit/api" ] && [ -f "/home/resinkit/.local/bin/resinkit-api-entrypoint.sh" ]; then
        echo "[RESINKIT] Resinkit API already installed (1/2)"
        # check if resinkit-api-entrypoint.sh is installed
        if [ -f "/home/resinkit/.local/bin/resinkit-api-entrypoint.sh" ]; then
            echo "[RESINKIT] Resinkit API entrypoint already installed (2/2)"
            return 0
        fi
    fi

    # clean up old resinkit-api folder
    rm -rf /opt/resinkit/api || true

    if [ -n "$RESINKIT_API_GITHUB_TOKEN" ]; then
        echo "[RESINKIT] RESINKIT_API_GITHUB_TOKEN is set, cloning from GitHub repository"
        # Clone the repository using GitHub PAT
        git clone "https://$RESINKIT_API_GITHUB_TOKEN@github.com/resink-ai/resinkit-api-python.git" /opt/resinkit/api
        echo "[RESINKIT] Resinkit API cloned from GitHub to /opt/resinkit/api"
    else
        echo "[RESINKIT] RESINKIT_API_GITHUB_TOKEN not set, using local resources"
        # Copy from local resources (original behavior)
        mkdir -p /opt/resinkit/api
        cp -rv "$ROOT_DIR/resources/resinkit-api" "/opt/resinkit/api"
        echo "[RESINKIT] Resinkit API copied from resources to /opt/resinkit/api"
    fi

    # Copy entrypoint script to the API directory
    mkdir -p /home/resinkit/.local/bin
    cp -v "$ROOT_DIR/resources/resinkit-api/resinkit-api-entrypoint.sh" "/home/resinkit/.local/bin/resinkit-api-entrypoint.sh"
    echo "[RESINKIT] Entrypoint script copied to /home/resinkit/.local/bin/resinkit-api-entrypoint.sh"
    chmod +x /home/resinkit/.local/bin/resinkit-api-entrypoint.sh
    chown -R resinkit:resinkit /opt/resinkit/api
    chown -R resinkit:resinkit /home/resinkit/.local/bin/resinkit-api-entrypoint.sh
}

install_resinkit_api
