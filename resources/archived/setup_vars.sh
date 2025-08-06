#!/bin/bash
# shellcheck disable=SC1091,SC2155

# Set up and validate all required variables for the ResInKit setup

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

# Function to check if running inside a container
is_container() {
    if [ -f /.dockerenv ] || (grep -sq 'docker\|lxc' /proc/1/cgroup); then
        echo "true"
    else
        echo "false"
    fi
}

# Function to check if running on an EC2 instance
is_ec2() {
    if curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/ &>/dev/null; then
        echo "true"
    else
        echo "false"
    fi
}

get_user_id() {
    # if is_ec2 is true, USER_ID must be set, otherwise raise error, otherwise we can fallback to $(id -u)
    if [ "$1" = "true" ]; then
        if [ -z "$USER_ID" ]; then
            echo "[RESINKIT] Error: USER_ID is not set"
            exit 1
        fi
        echo "$USER_ID"
    else
        echo ${USER_ID:-$(id -u)}
    fi
}

setup_vars() {
    # Validate critical environment variables if they're set from environment file
    if [ -f /etc/environment.seed ]; then
        . /etc/environment.seed
    fi

    if [ -f /etc/environment ]; then
        . /etc/environment
    fi

    # Check and report environment variables
    if [ -z "$FLINK_HOME" ] || [ -z "$RESINKIT_API_PATH" ] || [ -z "$RESINKIT_ENTRYPOINT_SH" ]; then
        echo "[RESINKIT] Warning: Some environment variables are not set"
        echo "[RESINKIT] FLINK_HOME: ${FLINK_HOME:-not set}"
        echo "[RESINKIT] RESINKIT_API_PATH: ${RESINKIT_API_PATH:-not set}"
        echo "[RESINKIT] RESINKIT_ENTRYPOINT_SH: ${RESINKIT_ENTRYPOINT_SH:-not set}"
    else
        echo "[RESINKIT] Environment variables validated"
    fi

    # Misc variables
    export IS_CONTAINER=${IS_CONTAINER:-$(is_container)}
    export IS_EC2=${IS_EC2:-$(is_ec2)}
    export USER_ID=$(get_user_id $IS_EC2)
    export X_RESINKIT_PAT=${X_RESINKIT_PAT:-pat_cnk8_}

    # Flink variables
    export FLINK_HOME=${FLINK_HOME:-/opt/flink}
    export FLINK_VER_MAJOR=${FLINK_VER_MAJOR:-1.20}
    export FLINK_VER_MINOR=${FLINK_VER_MINOR:-1.20.1}
    export FLINK_CDC_VER=${FLINK_CDC_VER:-3.4.0}
    export FLINK_PAIMON_VER=${FLINK_PAIMON_VER:-1.0.1}
    export FLINK_CDC_HOME=${FLINK_CDC_HOME:-/opt/flink-cdc}
    # Hadoop variables
    export HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
    export HADOOP_VERSION=${HADOOP_VERSION:-2.8.5}
    export APACHE_HADOOP_URL=${APACHE_HADOOP_URL:-https://archive.apache.org/dist/hadoop/}

    # Set HADOOP_CLASSPATH for Iceberg integration (following official Iceberg guide)
    if [ -f "$HADOOP_HOME/bin/hadoop" ]; then
        export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)
        echo "[RESINKIT] HADOOP_CLASSPATH set for Iceberg integration"
    else
        echo "[RESINKIT] Hadoop binary not found at $HADOOP_HOME/bin/hadoop, HADOOP_CLASSPATH not set"
    fi

    # ResInKit variables
    export RESINKIT_ROLE=${RESINKIT_ROLE:-resinkit}
    export RESINKIT_ROLE_HOME=${RESINKIT_ROLE_HOME:-/home/resinkit}
    export RESINKIT_API_PATH=${RESINKIT_API_PATH:-/opt/resinkit/api}
    export RESINKIT_ENTRYPOINT_SH=${RESINKIT_ENTRYPOINT_SH:-/opt/resinkit/resources/entrypoint.sh}
    export RESINKIT_API_VENV_DIR=${RESINKIT_API_VENV_DIR:-/opt/resinkit/api/.venv}
    export RESINKIT_API_LOG_FILE=${RESINKIT_API_LOG_FILE:-/opt/resinkit/api/resinkit_api.log}
    export RESINKIT_API_SERVICE_PORT=${RESINKIT_API_SERVICE_PORT:-8602}

    # Architecture detection (used in multiple functions)
    ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
    export ARCH

    # Java home path
    export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-${ARCH}}

    # Kafka home path
    export KAFKA_HOME=${KAFKA_HOME:-/opt/kafka}

    # MariaDB(MySQL) variables
    export MYSQL_RESINKIT_PASSWORD=${MYSQL_RESINKIT_PASSWORD:-resinkit_mysql_password}

    # setup .env.byoc in RESINKIT_API_PATH
    if [ -f "$RESINKIT_API_PATH/.env.byoc" ]; then
        echo "[RESINKIT] .env.byoc already exists, skipping"
    else
        echo "[RESINKIT] Creating .env.byoc"
        mkdir -p "$RESINKIT_API_PATH"
        echo "RESINKIT_API_PATH=$RESINKIT_API_PATH" >"$RESINKIT_API_PATH/.env.byoc"
        echo "X_RESINKIT_PAT=$X_RESINKIT_PAT" >>"$RESINKIT_API_PATH/.env.byoc"
        echo "[RESINKIT] .env.byoc created"
    fi

    if [[ -f /etc/environment ]] && grep -q "ARCH" /etc/environment && grep -q "PATH" /etc/environment; then
        echo "[RESINKIT] Environment variables already saved to /etc/environment, skipping"
    else
        {
            echo ""
            echo "ARCH=$ARCH"
            echo "JAVA_HOME=$JAVA_HOME"
            echo "HADOOP_HOME=$HADOOP_HOME"
            echo "IS_CONTAINER=$IS_CONTAINER"
            echo "IS_EC2=$IS_EC2"
            echo "USER_ID=$USER_ID"
            if [ -n "$HADOOP_CLASSPATH" ]; then
                echo "HADOOP_CLASSPATH=$HADOOP_CLASSPATH"
            fi
            echo "PATH=$JAVA_HOME/bin:$FLINK_HOME/bin:$KAFKA_HOME/bin:$HADOOP_HOME/bin"
            if [ -n "$RESINKIT_API_GITHUB_TOKEN" ]; then
                echo "RESINKIT_API_GITHUB_TOKEN=$RESINKIT_API_GITHUB_TOKEN"
            fi
        } >>/etc/environment
        echo "[RESINKIT] Environment variables set"
    fi
}
