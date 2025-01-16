#! /bin/bash

set -ex pipefail

function debian_install_common_packages() {
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
    groupadd --system --gid=9999 flink
    useradd --system --home-dir $FLINK_HOME --uid=9999 --gid=flink flink
    cd $FLINK_HOME

    set -ex
    wget -nv -O flink.tgz "$FLINK_TGZ_URL"

    if [ "$CHECK_GPG" = "true" ]; then
        wget -nv -O flink.tgz.asc "$FLINK_ASC_URL"
        export GNUPGHOME="$(mktemp -d)"
        for server in ha.pool.sks-keyservers.net $(
            shuf -e
            hkp://p80.pool.sks-keyservers.net:80
            keyserver.ubuntu.com
            hkp://keyserver.ubuntu.com:80
            pgp.mit.edu
        ); do
            gpg --batch --keyserver "$server" --recv-keys "$GPG_KEY" && break || :
        done
        gpg --batch --verify flink.tgz.asc flink.tgz
        gpgconf --kill all
        rm -rf "$GNUPGHOME" flink.tgz.asc
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
    export GOSU_VERSION=1.11
    wget -nv -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture)"
    wget -nv -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$(dpkg --print-architecture).asc"
    export GNUPGHOME="$(mktemp -d)"
    for server in ha.pool.sks-keyservers.net $(
        shuf -e
        hkp://p80.pool.sks-keyservers.net:80
        keyserver.ubuntu.com
        hkp://keyserver.ubuntu.com:80
        pgp.mit.edu
    ); do
        gpg --batch --keyserver "$server" --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 && break || :
    done
    gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu
    gpgconf --kill all
    rm -rf "$GNUPGHOME" /usr/local/bin/gosu.asc
    chmod +x /usr/local/bin/gosu
    gosu nobody true
}

################################################################################
# Function to show usage
function show_usage() {
    echo "Usage: $0 <command> [arguments]"
    echo "Available commands:"
    echo "  install_common_packages    - Install common packages"
    echo "  install_java    - Install Java"
    echo "  install_flink    - Install Flink"
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
"install_common_packages")
    debian_install_common_packages
    ;;
"install_java")
    debian_install_java
    ;;
"install_flink")
    debian_install_flink
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
