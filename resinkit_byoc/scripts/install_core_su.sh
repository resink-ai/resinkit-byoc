#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046,SC1090
set -eo pipefail
: "${ROOT_DIR:?}"

# Install Core components for resinkit user

function install_uv() {
    if ! command -v uv &>/dev/null; then
        echo "[RESINKIT] Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/home/resinkit/.local/bin" sh
    fi
}

function install_java_sdkman() {
    curl -s "https://get.sdkman.io?ci=true" | env SDKMAN_DIR="/opt/sdkman" bash
    sdk install java 17-zulu
    sdk install maven
}


function install_java() {
    

    ARCH=$(dpkg --print-architecture)
    export ARCH

    # Check if Java is already installed by checking /usr/lib/jvm/java-17-openjdk-amd64/bin/java
    if [ -f "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/java" ]; then
        echo "[RESINKIT] Java already installed, skipping"
        return 0
    fi
    apt-get update
    apt-get install -y openjdk-17-jdk openjdk-17-jre
    update-alternatives --set java "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/java"
    update-alternatives --set javac "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/javac"
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${ARCH}
    apt-get install -y --no-install-recommends maven
    mvn --version

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.java_installed
}


install_uv
install_java
