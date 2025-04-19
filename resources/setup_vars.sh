#!/bin/bash
# shellcheck disable=SC1091

# Set up and validate all required variables for the ResInKit setup

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

setup_vars() {
    # Set the ResInKit role
    export RESINKIT_ROLE='resinkit'

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
    export FLINK_HOME=${FLINK_HOME:-/opt/flink}
    export RESINKIT_API_PATH=${RESINKIT_API_PATH:-/opt/resinkit/api}
    export RESINKIT_ENTRYPOINT_SH=${RESINKIT_ENTRYPOINT_SH:-/opt/resinkit/entrypoint.sh}
    export RESINKIT_API_VENV_DIR=${RESINKIT_API_VENV_DIR:-/opt/resinkit/api/.venv}
    export RESINKIT_API_LOG_FILE=${RESINKIT_API_LOG_FILE:-/opt/resinkit/logs/resinkit_api.log}
    export RESINKIT_API_SERVICE_PORT=${RESINKIT_API_SERVICE_PORT:-8602}

    # Architecture detection (used in multiple functions)
    ARCH=$(dpkg --print-architecture 2>/dev/null || echo "amd64")
    export ARCH

    # Java home path
    export JAVA_HOME=${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-${ARCH}}

    # Kafka home path
    export KAFKA_HOME=${KAFKA_HOME:-/opt/kafka}

    if [[ -f /etc/environment ]] && grep -q "RESINKIT_API_PATH" /etc/environment && grep -q "RESINKIT_API_SERVICE_PORT" /etc/environment; then
        echo "[RESINKIT] Environment variables already saved to /etc/environment, skipping"
    else
        {
            echo ""
            echo "ARCH=$ARCH"
            echo "FLINK_HOME=$FLINK_HOME"
            echo "JAVA_HOME=$JAVA_HOME"
            echo "KAFKA_HOME=$KAFKA_HOME"
            echo "RESINKIT_API_PATH=$RESINKIT_API_PATH"
            echo "RESINKIT_ENTRYPOINT_SH=$RESINKIT_ENTRYPOINT_SH"
            echo "PATH=$JAVA_HOME/bin:$FLINK_HOME/bin:$KAFKA_HOME/bin:$PATH"
            echo "RESINKIT_API_VENV_DIR=$RESINKIT_API_VENV_DIR"
            echo "RESINKIT_API_LOG_FILE=$RESINKIT_API_LOG_FILE"
            echo "RESINKIT_API_SERVICE_PORT=$RESINKIT_API_SERVICE_PORT"
        } >>/etc/environment
        echo "[RESINKIT] Environment variables set"
    fi

    # Check for GitHub token if needed for private repositories
    if [ -z "$TF_VAR_RESINKIT_GITHUB_TOKEN" ]; then
        echo "[RESINKIT] Note: TF_VAR_RESINKIT_GITHUB_TOKEN is not set - may be required for some operations"
    fi
}
