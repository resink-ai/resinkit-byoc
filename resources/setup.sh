#! /bin/bash

set -eox pipefail

# if git rev-parse --show-toplevel works and is not empty, use the root folder as the root directory
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    ROOT_DIR=$(git rev-parse --show-toplevel)
else
    ROOT_DIR="/root/resinkit-byoc"
fi

RESINKIT_ROLE='resinkit'
RESINKIT_ENTRYPOINT_SH='/opt/resinkit/entrypoint.sh'

drop_privs_cmd() {
    if [ "$(id -u)" != 0 ]; then
        # Don't need to drop privs if EUID != 0
        return
    elif [ -x /sbin/su-exec ]; then
        # Alpine
        echo su-exec $RESINKIT_ROLE
    else
        # Others
        echo gosu $RESINKIT_ROLE
    fi
}

pre_setup() {
    # Check if git is installed
    if ! command -v git &>/dev/null; then
        apt-get update
        apt-get install -y --no-install-recommends git ca-certificates make
    fi

    # Check if the directory already exists
    if [ ! -d "$HOME/resinkit-byoc" ]; then
        git clone https://github.com/resink-ai/resinkit-byoc.git "$HOME/resinkit-byoc"
    else
        cd "$HOME/resinkit-byoc" && git pull
        echo "[RESINKIT] Directory $HOME/resinkit-byoc already exists, skipping git clone"
    fi

    # Only run setup if it hasn't been run before
    cd "$HOME/resinkit-byoc"
    if [ ! -f "$HOME/resinkit-byoc/.setup_completed" ]; then
        ./resources/setup.sh debian_all
        touch "$HOME/resinkit-byoc/.setup_completed"
    else
        echo "[RESINKIT] Setup already completed, skipping"
    fi
}

post_setup() {
    # make sure FLINK_HOME is set
    if [ -z "$FLINK_HOME" ] || [ -z "$RESINKIT_API_PATH" ] || [ -z "$RESINKIT_ENTRYPOINT_SH" ]; then
        # shellcheck disable=SC1091
        . /etc/environment
    fi

    if [ -z "$FLINK_HOME" ] || [ -z "$RESINKIT_API_PATH" ] || [ -z "$RESINKIT_ENTRYPOINT_SH" ]; then
        echo "[RESINKIT] Error: FLINK_HOME or RESINKIT_API_PATH or RESINKIT_ENTRYPOINT_SH is not set"
        echo "[RESINKIT] FLINK_HOME: $FLINK_HOME"
        echo "[RESINKIT] RESINKIT_API_PATH: $RESINKIT_API_PATH"
        echo "[RESINKIT] RESINKIT_ENTRYPOINT_SH: $RESINKIT_ENTRYPOINT_SH"
        return 1
    fi

    # Check if entrypoint.sh already exists
    if [ ! -f "$RESINKIT_ENTRYPOINT_SH" ]; then
        cp -v "$ROOT_DIR/resources/entrypoint.sh" $RESINKIT_ENTRYPOINT_SH
    else
        echo "[RESINKIT] Entrypoint script already exists at $RESINKIT_ENTRYPOINT_SH, skipping copy"
    fi

    # Check if already executed
    if [ -f "/opt/setup/.post_setup_completed" ]; then
        echo "[RESINKIT] Post-setup already completed, skipping"
        return 0
    fi

    # Create marker file
    mkdir -p "$(dirname $RESINKIT_ENTRYPOINT_SH)" # Keep this for the entrypoint script itself
    mkdir -p "/opt/setup"
    touch "/opt/setup/.post_setup_completed"

    exec $(drop_privs_cmd) $RESINKIT_ENTRYPOINT_SH
}

# verify_gpg_signature <file> <signature_file> <gpg_key> [retries]
verify_gpg_signature() {
    local file="$1"         # Original file to verify
    local sig_file="$2"     # Path to the signature file
    local gpg_key="$3"      # GPG key to verify against
    local retries="${4:-3}" # Number of retries, default 3

    # Validate required parameters
    if [[ -z "$file" || -z "$sig_file" || -z "$gpg_key" ]]; then
        echo "[RESINKIT] Usage: verify_gpg_signature <file> <signature_file> <gpg_key> [retries]"
        return 1
    fi

    # Check if original file exists
    if [[ ! -f "$file" ]]; then
        echo "[RESINKIT] Error: File '$file' not found"
        return 1
    fi

    # Check if signature file exists
    if [[ ! -f "$sig_file" ]]; then
        echo "[RESINKIT] Error: Signature file '$sig_file' not found"
        return 1
    fi

    # Create temporary GPG home directory
    GNUPGHOME="$(mktemp -d)"

    # Define reliable keyservers
    local key_servers=(
        "keyserver.ubuntu.com"
        "hkp://keyserver.ubuntu.com:80"
        "keys.openpgp.org"
        "hkps://keys.openpgp.org"
        "pgp.mit.edu"
        "hkp://pgp.mit.edu:80"
        "keyring.debian.org"
        "hkp://keyring.debian.org:80"
    )

    # Try to import the GPG key
    local key_imported=0
    local attempt=1
    while [[ $attempt -le $retries && $key_imported -eq 0 ]]; do
        echo "[RESINKIT] Attempt $attempt of $retries to import GPG key..."
        for server in "${key_servers[@]}"; do
            echo "[RESINKIT] Trying keyserver: $server"
            if gpg --batch --keyserver "$server" --recv-keys "$gpg_key" 2>/dev/null; then
                key_imported=1
                break
            fi
            sleep 1
        done

        ((attempt++))
    done

    # Check if key import was successful
    if [[ $key_imported -eq 0 ]]; then
        echo "[RESINKIT] Error: Failed to import GPG key after $retries attempts"
        rm -rf "$GNUPGHOME"
        return 1
    fi

    # Verify the signature
    local verify_result=0
    if ! gpg --batch --verify "$sig_file" "$file" 2>/dev/null; then
        echo "[RESINKIT] Error: GPG verification failed for $file"
        verify_result=1
    else
        echo "[RESINKIT] GPG verification successful for $file"
    fi

    # Cleanup
    gpgconf --kill all
    rm -rf "$GNUPGHOME"

    return $verify_result
}

function debian_install_common_packages() {
    # Check if packages are already installed
    if [ -f "/opt/setup/.common_packages_installed" ]; then
        echo "[RESINKIT] Common packages already installed, skipping"
        return 0
    fi

    export TZ=UTC
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y \
        vim \
        wget \
        gnupg \
        nginx \
        python3-pip \
        python3-dev \
        libpcre3-dev \
        iputils-ping \
        mysql-client \
        telnet \
        bash &&
        apt-get clean

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.common_packages_installed
}

function debian_install_envs() {
    if grep -q "FLINK_HOME=/opt/flink" /etc/environment; then
        echo "[RESINKIT] Environment variables already set, skipping"
        return 0
    fi
    {
        echo "FLINK_HOME=/opt/flink"
        echo "JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${ARCH}"
        echo "KAFKA_HOME=/opt/kafka"
        echo "RESINKIT_API_PATH=/opt/resinkit/api"
        echo "PATH=$JAVA_HOME/bin:$FLINK_HOME/bin:$KAFKA_HOME/bin:$PATH"
    } >>/etc/environment

    # shellcheck disable=SC1091
    source /etc/environment
}

function debian_install_java() {
    # Check if Java is already installed
    if [ -f "/opt/setup/.java_installed" ]; then
        echo "[RESINKIT] Java already installed, skipping"
        return 0
    fi

    ARCH=$(dpkg --print-architecture)
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

# see https://github.com/apache/flink-docker/blob/f77b347d0a534da0482e692d80f559f47041829e/1.19/scala_2.12-java17-ubuntu/Dockerfile
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

    if ! getent group $RESINKIT_ROLE >/dev/null; then
        groupadd --system --gid=9999 $RESINKIT_ROLE
    fi

    if ! getent passwd $RESINKIT_ROLE >/dev/null; then
        useradd --system --home-dir $FLINK_HOME --uid=9999 --gid=$RESINKIT_ROLE $RESINKIT_ROLE
    fi
    cd $FLINK_HOME

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
    # save list of currently installed packages for later so we can clean up
    savedAptMark="$(apt-mark showmanual)"
    # apt-get update
    apt-get install -y --no-install-recommends ca-certificates gnupg wget
    rm -rf /var/lib/apt/lists/*
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"
    wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"
    wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"
    # verify the signature
    local GOSU_GPG_KEY=B42F6819007F00F88E364FD4036A9C25BF357DD4
    verify_gpg_signature /usr/local/bin/gosu /usr/local/bin/gosu.asc $GOSU_GPG_KEY
    # clean up fetch dependencies
    apt-mark auto '.*' >/dev/null
    [ -z "$savedAptMark" ] || apt-mark manual "$savedAptMark"
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
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
        cd "$ROOT_DIR/resources/flink/lib"
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
    if [ -d "$ROOT_DIR/api/resinkit_api/" ] && [ -f "/opt/setup/.resinkit_installed" ]; then
        echo "[RESINKIT] Resinkit already installed, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing resinkit..."
    if [[ -d "$ROOT_DIR/api/resinkit_api" ]]; then
        echo "[RESINKIT] Resinkit API directory already exists, skipping clone"
    elif [ -z "$TF_VAR_RESINKIT_GITHUB_TOKEN" ]; then
        echo "[RESINKIT] Error: TF_VAR_RESINKIT_GITHUB_TOKEN is not set"
        return 1
    else
        # git clone with github token
        git clone "https://${TF_VAR_RESINKIT_GITHUB_TOKEN}@github.com/resink-ai/resinkit-api.git" "$ROOT_DIR/api"
        echo "[RESINKIT] Resinkit API cloned"
    fi

    # Copy api/ to /opt/resinkit/resinkit_api
    cp -rv "$ROOT_DIR/api" "$RESINKIT_API_PATH"
    echo "[RESINKIT] Resinkit API copied"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.resinkit_installed
}

function debian_setup_nginx() {
    # Check if nginx is already setup
    if [ -f "/opt/setup/.nginx_setup_completed" ]; then
        echo "[RESINKIT] Nginx already setup, skipping"
        return 0
    fi

    # Copy the Nginx configuration file
    rm /etc/nginx/sites-available/resinkit_nginx.conf
    rm /etc/nginx/sites-enabled/resinkit_nginx.conf
    cp -v "$ROOT_DIR/resources/nginx/resinkit_nginx.conf" /etc/nginx/sites-available/resinkit_nginx.conf
    ln -sf /etc/nginx/sites-available/resinkit_nginx.conf /etc/nginx/sites-enabled/resinkit_nginx.conf

    # Test the Nginx configuration
    nginx -t

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.nginx_setup_completed
}

################################################################################
# Function to show usage
function show_usage() {
    set +x
    echo "[RESINKIT] Usage: $0 <command> [arguments]"
    echo "[RESINKIT] Available commands:"
    echo "[RESINKIT]   debian_install_common_packages   - Install common packages"
    echo "[RESINKIT]   debian_install_java              - Install Java"
    echo "[RESINKIT]   debian_install_flink             - Install Flink"
    echo "[RESINKIT]   debian_install_kafka             - Install Kafka"
    echo "[RESINKIT]   debian_install_flink_jars        - Install Flink jars"
    echo "[RESINKIT]   debian_install_resinkit          - Install resinkit"
    echo "[RESINKIT]   debian_install_gosu              - Install gosu"
    echo "[RESINKIT]   debian_install_envs              - Install environment variables"
    echo "[RESINKIT]   debian_all                       - Install all"
    echo "[RESINKIT]   help                             - Show usage"
}

# Main argument parsing
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Get the command (first argument)
cmd=$1
shift # Remove the first argument, leaving any remaining args

# Parse command and execute corresponding function
case $cmd in
"debian_install_common_packages")
    debian_install_common_packages
    ;;
"debian_install_java")
    debian_install_java
    ;;
"debian_install_flink")
    debian_install_flink
    ;;
"debian_install_gosu")
    debian_install_gosu
    ;;
"debian_install_envs")
    debian_install_envs
    ;;
"debian_install_kafka")
    debian_install_kafka
    ;;
"debian_install_flink_jars")
    debian_install_flink_jars
    ;;
"debian_install_resinkit")
    debian_install_resinkit
    ;;
"debian_setup_nginx")
    debian_setup_nginx
    ;;
"debian_all")
    debian_install_common_packages
    debian_install_java
    debian_install_flink
    debian_install_gosu
    debian_install_envs
    debian_install_kafka
    debian_install_flink_jars
    debian_install_resinkit
    debian_setup_nginx
    post_setup
    ;;
"help" | "-h" | "--help")
    show_usage
    ;;
*)
    echo "[RESINKIT] Error: Unknown command '$cmd'"
    show_usage
    exit 1
    ;;
esac
