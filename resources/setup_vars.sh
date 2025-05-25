#!/bin/bash
# shellcheck disable=SC1091

# Set up and validate all required variables for the ResInKit setup

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

setup_vars() {
    # Validate critical environment variables if they're set from environment file
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

    # Set default paths if not already set
    export RESINKIT_ROLE=${RESINKIT_ROLE:-resinkit}
    export FLINK_HOME=${FLINK_HOME:-/opt/flink}
    export FLINK_CDC_HOME=${FLINK_CDC_HOME:-/opt/flink-cdc}
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

    # MinIO configuration
    export MINIO_ROOT_USER=${MINIO_ROOT_USER:-admin}
    export MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-minio123}
    export MINIO_DATA_DIR=${MINIO_DATA_DIR:-/opt/minio/data}
    export MINIO_CONFIG_DIR=${MINIO_CONFIG_DIR:-/opt/minio/config}
    export MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT:-9001}
    export MINIO_API_PORT=${MINIO_API_PORT:-9000}

    # setup .env.byoc in RESINKIT_API_PATH
    if [ -f "$RESINKIT_API_PATH/.env.byoc" ]; then
        echo "[RESINKIT] .env.byoc already exists, skipping"
    else
        echo "[RESINKIT] Creating .env.byoc"
        mkdir -p "$RESINKIT_API_PATH"
        echo "RESINKIT_API_PATH=$RESINKIT_API_PATH" >"$RESINKIT_API_PATH/.env.byoc"
        echo "X_RESINKIT_PAT='pat_cnk8_'" >>"$RESINKIT_API_PATH/.env.byoc"
        echo "[RESINKIT] .env.byoc created"
    fi

    if [[ -f /etc/environment ]] && grep -q "RESINKIT_API_PATH" /etc/environment && grep -q "RESINKIT_API_SERVICE_PORT" /etc/environment; then
        echo "[RESINKIT] Environment variables already saved to /etc/environment, skipping"
    else
        {
            echo ""
            echo "RESINKIT_ROLE=$RESINKIT_ROLE"
            echo "ARCH=$ARCH"
            echo "FLINK_HOME=$FLINK_HOME"
            echo "JAVA_HOME=$JAVA_HOME"
            echo "KAFKA_HOME=$KAFKA_HOME"
            echo "FLINK_CDC_HOME=$FLINK_CDC_HOME"
            echo "RESINKIT_API_PATH=$RESINKIT_API_PATH"
            echo "RESINKIT_ENTRYPOINT_SH=$RESINKIT_ENTRYPOINT_SH"
            echo "PATH=$JAVA_HOME/bin:$FLINK_HOME/bin:$KAFKA_HOME/bin:/opt/minio/bin:$PATH"
            echo "RESINKIT_API_VENV_DIR=$RESINKIT_API_VENV_DIR"
            echo "RESINKIT_API_LOG_FILE=$RESINKIT_API_LOG_FILE"
            echo "RESINKIT_API_SERVICE_PORT=$RESINKIT_API_SERVICE_PORT"
            echo "MINIO_ROOT_USER=$MINIO_ROOT_USER"
            echo "MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD"
            echo "MINIO_DATA_DIR=$MINIO_DATA_DIR"
            echo "MINIO_CONFIG_DIR=$MINIO_CONFIG_DIR"
            echo "MINIO_CONSOLE_PORT=$MINIO_CONSOLE_PORT"
            echo "MINIO_API_PORT=$MINIO_API_PORT"
        } >>/etc/environment
        echo "[RESINKIT] Environment variables set"
    fi
}
