#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046

function install_common_packages() {
    # Check if packages are already installed
    if [ -f "/opt/setup/.common_packages_installed" ]; then
        echo "[RESINKIT] Common packages already installed, skipping"
        return 0
    fi

    export TZ=UTC
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
        vim \
        wget \
        gnupg \
        nginx \
        iputils-ping \
        mariadb-client \
        telnet \
        ca-certificates \
        gnupg \
        git \
        ca-certificates \
        make \
        curl \
        zsh \
        wget
    apt-get install -y --no-install-recommends \
        build-essential \
        zlib1g-dev \
        libncurses5-dev \
        libgdbm-dev \
        libnss3-dev \
        libssl-dev \
        libreadline-dev \
        libffi-dev \
        libsqlite3-dev \
        libbz2-dev \
        pkg-config \
        liblzma-dev

    apt-get install -y python3 python3-pip python3-dev python3-venv libpcre3-dev

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.common_packages_installed
}

