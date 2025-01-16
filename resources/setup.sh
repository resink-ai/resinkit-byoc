#! /bin/bash

set -eox pipefail

pre_setup() {
    apt-get update
    apt-get install -y --no-install-recommends git ca-certificates
    cd $HOME
    git clone https://github.com/resink-ai/resinkit-byoc.git
    cd resinkit-byoc
}

# verify_gpg_signature <file> <signature_file> <gpg_key> [retries]
verify_gpg_signature() {
    local file="$1"         # Original file to verify
    local sig_file="$2"     # Path to the signature file
    local gpg_key="$3"      # GPG key to verify against
    local retries="${4:-3}" # Number of retries, default 3

    # Validate required parameters
    if [[ -z "$file" || -z "$sig_file" || -z "$gpg_key" ]]; then
        echo "Usage: verify_gpg_signature <file> <signature_file> <gpg_key> [retries]"
        return 1
    fi

    # Check if original file exists
    if [[ ! -f "$file" ]]; then
        echo "Error: File '$file' not found"
        return 1
    fi

    # Check if signature file exists
    if [[ ! -f "$sig_file" ]]; then
        echo "Error: Signature file '$sig_file' not found"
        return 1
    fi

    # Create temporary GPG home directory
    local GNUPGHOME="$(mktemp -d)"
    export GNUPGHOME

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
        echo "Attempt $attempt of $retries to import GPG key..."
        for server in "${key_servers[@]}"; do
            echo "Trying keyserver: $server"
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
        echo "Error: Failed to import GPG key after $retries attempts"
        rm -rf "$GNUPGHOME"
        return 1
    fi

    # Verify the signature
    local verify_result=0
    if ! gpg --batch --verify "$sig_file" "$file" 2>/dev/null; then
        echo "Error: GPG verification failed for $file"
        verify_result=1
    else
        echo "GPG verification successful for $file"
    fi

    # Cleanup
    gpgconf --kill all
    rm -rf "$GNUPGHOME"

    return $verify_result
}

function debian_install_common_packages() {
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
}

function debian_set_etc_environment() {
    if grep -q "FLINK_HOME=/opt/flink" /etc/environment; then
        return
    fi
    echo "FLINK_HOME=/opt/flink" >>/etc/environment
    echo "PATH=$FLINK_HOME/bin:$PATH" >>/etc/environment
}

function debian_install_java() {
    ARCH=$(dpkg --print-architecture)
    apt-get install -y openjdk-17-jdk openjdk-17-jre
    update-alternatives --set java "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/java"
    update-alternatives --set javac "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/javac"
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${ARCH}
}

# see https://github.com/apache/flink-docker/blob/f77b347d0a534da0482e692d80f559f47041829e/1.19/scala_2.12-java17-ubuntu/Dockerfile
function debian_install_flink() {
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

    if ! getent group flink >/dev/null; then
        groupadd --system --gid=9999 flink
    fi

    if ! getent passwd flink >/dev/null; then
        useradd --system --home-dir $FLINK_HOME --uid=9999 --gid=flink flink
    fi
    cd $FLINK_HOME

    wget -nv -O flink.tgz "$FLINK_TGZ_URL"

    if [ "$CHECK_GPG" = "true" ]; then
        wget -nv -O flink.tgz.asc "$FLINK_ASC_URL"
        verify_gpg_signature flink.tgz flink.tgz.asc $GPG_KEY
    fi

    tar -xf flink.tgz --strip-components=1
    rm flink.tgz

    chown -R flink:flink .

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

}

function debian_install_gosu() {
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
    [ -z "$savedAptMark" ] || apt-mark manual $savedAptMark
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
    chmod +x /usr/local/bin/gosu
    # verify that the binary works
    gosu --version
    gosu nobody true
}

################################################################################
# Function to show usage
function show_usage() {
    set +x
    echo "Usage: $0 <command> [arguments]"
    echo "Available commands:"
    echo "  debian_install_common_packages    - Install common packages"
    echo "  debian_install_java    - Install Java"
    echo "  debian_install_flink    - Install Flink"
    echo "  debian_install_gosu    - Install Flink entrypoint"
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
"debian_all")
    debian_install_common_packages
    debian_install_java
    debian_install_flink
    debian_install_gosu
    ;;
"help" | "-h" | "--help")
    show_usage
    ;;
*)
    echo "Error: Unknown command '$cmd'"
    show_usage
    exit 1
    ;;
esac
