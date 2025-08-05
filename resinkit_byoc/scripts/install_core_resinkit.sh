#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046,SC1090
set -eo pipefail
: "${ROOT_DIR:?}" "${RESINKIT_ROLE:?}"

# Install Core components for resinkit user

function install_uv() {
    if ! command -v uv &>/dev/null; then
        echo "[RESINKIT] Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source "/home/$RESINKIT_ROLE/.local/bin/env"
    fi
}

function install_java() {
    curl -s "https://get.sdkman.io?ci=true" | bash
    source "/home/$RESINKIT_ROLE/.sdkman/bin/sdkman-init.sh"
    sdk install java 17-zulu
    sdk install maven
}


install_uv
install_java
