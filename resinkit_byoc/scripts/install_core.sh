#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046
set -eo pipefail
: "${ROOT_DIR:?}" "${RESINKIT_ROLE:?}" "${RESINKIT_API_PATH:?}" 


function install_gosu() {
    # Check if gosu is already installed by check if /usr/local/bin/gosu exists
    if [ -f "/usr/local/bin/gosu" ]; then
        echo "[RESINKIT] gosu already installed, skipping"
        return 0
    fi

    # Grab gosu for easy step-down from root
    export GOSU_VERSION=1.17
    rm -rf /var/lib/apt/lists/*
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"
    wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"
    wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"
    # verify the signature
    local GOSU_GPG_KEY=B42F6819007F00F88E364FD4036A9C25BF357DD4
    verify_gpg_signature /usr/local/bin/gosu /usr/local/bin/gosu.asc $GOSU_GPG_KEY
    chmod +x /usr/local/bin/gosu
    # verify that the binary works
    gosu --version
    gosu nobody true
}


function install_nginx() {
    # Check if nginx is already setup
    if [ -f "/opt/setup/.nginx_installed" ]; then
        echo "[RESINKIT] Nginx already setup, skipping"
        return 0
    fi

    apt-get update && apt-get install --no-install-recommends -y nginx

    # Copy the Nginx configuration files
    # Install the main default site configuration
    cp -v "$ROOT_DIR/resources/nginx/default" /etc/nginx/sites-available/default

    # Install the reusable locations configuration
    cp -v "$ROOT_DIR/resources/nginx/resinkit_locations.conf" /etc/nginx/sites-available/resinkit_locations.conf

    # Enable the default site (create symlink if it doesn't exist)
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

    # Clean up old configuration files if they exist
    rm -vf /etc/nginx/sites-available/resinkit_nginx.conf || true
    rm -vf /etc/nginx/sites-enabled/resinkit_nginx.conf || true

    # Test the Nginx configuration
    nginx -t

    echo "[RESINKIT] Enabling and restarting nginx"
    systemctl enable nginx || true
    systemctl restart nginx || true
    systemctl status nginx || true

    service nginx reload || true
    service nginx status || true

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.nginx_installed
}

function install_kafka() {
    # Check if Kafka is already installed by checking if /opt/kafka exists and /opt/kafka/config/server.properties exists
    if [ -d "/opt/kafka" ] && [ -f "/opt/kafka/config/server.properties" ]; then
        echo "[RESINKIT] Kafka already installed, skipping"
        return 0
    fi

    wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz &&
        tar -xzf /tmp/kafka.tgz -C /opt &&
        mv /opt/kafka_2.12-3.4.0 /opt/kafka &&
        rm /tmp/kafka.tgz

    cp -v "$ROOT_DIR/resources/kafka/server.properties" "/opt/kafka/config/server.properties"

    mkdir -p /opt/kafka/logs
    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE /opt/kafka
    chmod -R 755 /opt/kafka/logs
}

function install_jupyter() {
    # copy resinkit_sample_project to /home/$RESINKIT_ROLE/
    cp -r "$ROOT_DIR/resources/jupyter/resinkit_sample_project" /home/$RESINKIT_ROLE/
    # copy jupyter_entrypoint.sh to /home/$RESINKIT_ROLE/.local/bin/
    cp "$ROOT_DIR/resources/jupyter/jupyter_entrypoint.sh" /home/$RESINKIT_ROLE/.local/bin/
    chmod +x /home/$RESINKIT_ROLE/.local/bin/jupyter_entrypoint.sh
    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE /home/$RESINKIT_ROLE/resinkit_sample_project
}

function install_resinkit_api() {
    if [ -n "$RESINKIT_API_GITHUB_TOKEN" ]; then
        echo "[RESINKIT] RESINKIT_API_GITHUB_TOKEN is set, cloning from GitHub repository"
        # Clone the repository using GitHub PAT
        git clone "https://$RESINKIT_API_GITHUB_TOKEN@github.com/resink-ai/resinkit-api-python.git" "$RESINKIT_API_PATH"
        echo "[RESINKIT] Resinkit API cloned from GitHub to $RESINKIT_API_PATH"
        # Copy entrypoint script to the API directory
        cp -v "$ROOT_DIR/resources/resinkit-api/resinkit-api-entrypoint.sh" "/home/$RESINKIT_ROLE/.local/bin/"
        echo "[RESINKIT] Entrypoint script copied to $RESINKIT_API_PATH"
    else
        echo "[RESINKIT] RESINKIT_API_GITHUB_TOKEN not set, using local resources"
        # Copy from local resources (original behavior)
        cp -rv "$ROOT_DIR/resources/resinkit-api" "$RESINKIT_API_PATH"
        echo "[RESINKIT] Resinkit API copied from resources to $RESINKIT_API_PATH"
    fi
}


install_gosu
install_nginx
install_kafka
install_jupyter
install_resinkit_api