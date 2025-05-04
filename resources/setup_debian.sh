#!/bin/bash
# shellcheck disable=SC1091,SC2086

# Debian-specific installation functions for ResInKit

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

# Source the common functions and variables
source "$ROOT_DIR/resources/setup_vars.sh"
source "$ROOT_DIR/resources/setup_common.sh"

function debian_install_common_packages() {
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

function debian_install_java() {
    # Check if Java is already installed
    if [ -f "/opt/setup/.java_installed" ]; then
        echo "[RESINKIT] Java already installed, skipping"
        return 0
    fi

    ARCH=$(dpkg --print-architecture)
    export ARCH
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

function debian_install_flink() {
    # Check if Flink is already installed
    if [ -d "/opt/flink" ] && [ -f "/opt/setup/.flink_installed" ]; then
        echo "[RESINKIT] Flink already installed, skipping"
        return 0
    fi

    apt-get -y install gpg libsnappy1v5 gettext-base libjemalloc-dev
    rm -rf /var/lib/apt/lists/*
    # skip install gosu
    export FLINK_TGZ_URL=https://dlcdn.apache.org/flink/flink-1.19.1/flink-1.19.1-bin-scala_2.12.tgz
    export FLINK_ASC_URL=https://downloads.apache.org/flink/flink-1.19.1/flink-1.19.1-bin-scala_2.12.tgz.asc
    export GPG_KEY=6378E37EB3AAEA188B9CB0D396C2914BB78A5EA1
    export CHECK_GPG=true
    export FLINK_HOME=/opt/flink
    export PATH=$FLINK_HOME/bin:$PATH
    mkdir -p $FLINK_HOME

    if ! getent group "$RESINKIT_ROLE" >/dev/null; then
        groupadd --system --gid=9999 "$RESINKIT_ROLE"
    fi

    if ! getent passwd $RESINKIT_ROLE >/dev/null; then
        useradd --system --home-dir "$FLINK_HOME" --uid=9999 --gid="$RESINKIT_ROLE" "$RESINKIT_ROLE"
    fi
    cd "$FLINK_HOME" || exit 1

    wget -nv -O flink.tgz "$FLINK_TGZ_URL"

    if [ "$CHECK_GPG" = "true" ]; then
        wget -nv -O flink.tgz.asc "$FLINK_ASC_URL"
        verify_gpg_signature flink.tgz flink.tgz.asc $GPG_KEY
    fi

    tar -xf flink.tgz --strip-components=1
    rm flink.tgz

    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE $FLINK_HOME

    # Replace default REST/RPC endpoint bind address to use the container's network interface
    CONF_FILE="$FLINK_HOME/conf/flink-conf.yaml"
    if [ ! -e "$FLINK_HOME/conf/flink-conf.yaml" ]; then
        CONF_FILE="${FLINK_HOME}/conf/config.yaml"
        /bin/bash "$FLINK_HOME/bin/config-parser-utils.sh" "${FLINK_HOME}/conf" "${FLINK_HOME}/bin" "${FLINK_HOME}/lib" \
            "-repKV" "rest.address,localhost,0.0.0.0" \
            "-repKV" "rest.bind-address,localhost,0.0.0.0" \
            "-repKV" "jobmanager.bind-host,localhost,0.0.0.0" \
            "-repKV" "taskmanager.bind-host,localhost,0.0.0.0" \
            "-rmKV" "taskmanager.host=localhost"
    else
        sed -i 's/rest.address: localhost/rest.address: 0.0.0.0/g' "$CONF_FILE"
        sed -i 's/rest.bind-address: localhost/rest.bind-address: 0.0.0.0/g' "$CONF_FILE"
        sed -i 's/jobmanager.bind-host: localhost/jobmanager.bind-host: 0.0.0.0/g' "$CONF_FILE"
        sed -i 's/taskmanager.bind-host: localhost/taskmanager.bind-host: 0.0.0.0/g' "$CONF_FILE"
        sed -i '/taskmanager.host: localhost/d' "$CONF_FILE"
    fi

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.flink_installed
}

function debian_install_gosu() {
    # Check if gosu is already installed
    if [ -f "/usr/local/bin/gosu" ] && [ -f "/opt/setup/.gosu_installed" ]; then
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

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.gosu_installed
}

function debian_install_kafka() {
    # Check if Kafka is already installed
    if [ -d "/opt/kafka" ] && [ -f "/opt/setup/.kafka_installed" ]; then
        echo "[RESINKIT] Kafka already installed, skipping"
        return 0
    fi

    wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz &&
        tar -xzf /tmp/kafka.tgz -C /opt &&
        mv /opt/kafka_2.12-3.4.0 /opt/kafka &&
        rm /tmp/kafka.tgz

    cp -v "$ROOT_DIR/resources/kafka/server.properties" /opt/kafka/config/server.properties

    mkdir -p /opt/kafka/logs
    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE /opt/kafka
    chmod -R 755 /opt/kafka/logs

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.kafka_installed
}

function debian_install_flink_jars() {
    # Check if Flink jars are already installed
    if [ -d "/opt/flink-cdc-3.2.1" ] && [ -f "/opt/setup/.flink_jars_installed" ]; then
        echo "[RESINKIT] Flink jars already installed, skipping"
        return 0
    fi

    # Download and extract Flink CDC if not already done
    if [ ! -d "/opt/flink-cdc-3.2.1" ]; then
        wget https://dlcdn.apache.org/flink/flink-cdc-3.2.1/flink-cdc-3.2.1-bin.tar.gz -O /tmp/flink-cdc-3.2.1-bin.tar.gz &&
            tar -xzf /tmp/flink-cdc-3.2.1-bin.tar.gz -C /opt/ &&
            rm /tmp/flink-cdc-3.2.1-bin.tar.gz
    else
        echo "[RESINKIT] Flink CDC directory already exists, skipping extraction"
    fi

    # Download required JAR files if needed
    (
        cd "$ROOT_DIR/resources/flink/lib" || exit 1
        bash download.sh
    )

    # Copy all required JAR files for Flink CDC connectors
    mkdir -p /opt/flink-cdc-3.2.1/lib/ /opt/flink/lib/ /opt/flink/cdc/
    cp -v "$ROOT_DIR/resources/flink/lib/flink-cdc-pipeline-connector-mysql-3.2.1.jar" /opt/flink-cdc-3.2.1/lib/
    cp -v "$ROOT_DIR/resources/flink/lib/flink-cdc-pipeline-connector-kafka-3.2.1.jar" /opt/flink-cdc-3.2.1/lib/
    cp -v "$ROOT_DIR/resources/flink/lib/flink-cdc-pipeline-connector-doris-3.2.1.jar" /opt/flink-cdc-3.2.1/lib/
    cp -v "$ROOT_DIR/resources/flink/lib/mysql-connector-java-8.0.27.jar" /opt/flink/lib/
    cp -v "$ROOT_DIR/resources/flink/lib/paimon-flink-1.19-0.9.0.jar" /opt/flink/lib/
    cp -v "$ROOT_DIR/resources/flink/lib/paimon-flink-action-0.9.0.jar" /opt/flink/lib/
    cp -v "$ROOT_DIR/resources/flink/lib/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar" /opt/flink/lib/

    # Copy configuration files
    mkdir -p /opt/flink/conf/ /opt/flink/cdc/
    cp -v "$ROOT_DIR/resources/flink/conf/conf.yaml" /opt/flink/conf/config.yaml
    cp -v "$ROOT_DIR/resources/flink/conf/log4j.properties" /opt/flink/conf/log4j.properties
    cp -rv "$ROOT_DIR/resources/flink/cdc/" /opt/flink/cdc/

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.flink_jars_installed
}

function debian_install_resinkit() {
    # Check if resinkit is already installed
    if [ -f "/opt/setup/.resinkit_installed" ]; then
        echo "[RESINKIT] Resinkit already installed, skipping"
        return 0
    fi

    if [ -d "$RESINKIT_API_PATH" ]; then
        echo "[RESINKIT] Resinkit API directory ($RESINKIT_API_PATH) already exists, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing resinkit..."

    # Verify that the api directory exists in the repo
    if [ ! -d "$ROOT_DIR/api" ]; then
        echo "[RESINKIT] Error: API directory not found at $ROOT_DIR/api"
        return 1
    fi

    # Copy api/ to resinkit api path
    mkdir -p "$(dirname "$RESINKIT_API_PATH")"
    rm -rf "$RESINKIT_API_PATH"
    cp -rv "$ROOT_DIR/api" "$RESINKIT_API_PATH"
    echo "[RESINKIT] Resinkit API copied"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.resinkit_installed
}

function debian_install_nginx() {
    # Check if nginx is already setup
    if [ -f "/opt/setup/.nginx_setup_completed" ]; then
        echo "[RESINKIT] Nginx already setup, skipping"
        return 0
    fi

    apt-get update && apt-get install --no-install-recommends -y nginx

    # Copy the Nginx configuration file
    rm -f /etc/nginx/sites-available/resinkit_nginx.conf
    rm -f /etc/nginx/sites-enabled/resinkit_nginx.conf
    cp -v "$ROOT_DIR/resources/nginx/resinkit_nginx.conf" /etc/nginx/sites-available/resinkit_nginx.conf
    ln -sf /etc/nginx/sites-available/resinkit_nginx.conf /etc/nginx/sites-enabled/resinkit_nginx.conf

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
    touch /opt/setup/.nginx_setup_completed
}

function debian_install_admin_tools() {
    apt update
    apt install -y curl jq lsof net-tools
}

function debian_install_all() {
    debian_install_common_packages
    debian_install_java
    debian_install_flink
    debian_install_gosu
    debian_install_kafka
    debian_install_flink_jars
    debian_install_resinkit
    debian_install_nginx
    debian_install_admin_tools

    echo "----------------------------------------"
    echo "[RESINKIT] ✅ Installation completed"
    echo "----------------------------------------"
}
