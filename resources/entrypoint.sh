#!/bin/bash

# Ensure required environment variables are set
if [ -z "${KAFKA_HOME}" ] || [ -z "${FLINK_HOME}" ] || [ -z "${RESINKIT_API_VENV_DIR}" ]; then
    # shellcheck disable=SC1091
    . /etc/environment
fi

# Start Kafka
"${KAFKA_HOME}/bin/zookeeper-server-start.sh" "${KAFKA_HOME}/config/zookeeper.properties" &
"${KAFKA_HOME}/bin/kafka-server-start.sh" "${KAFKA_HOME}/config/server.properties" &

# Start Flink session cluster & SQL gateway
"${FLINK_HOME}/bin/start-cluster.sh"
"${FLINK_HOME}/bin/sql-gateway.sh" start -Dsql-gateway.endpoint.rest.address=localhost

# if venv exists, start the service
if [ -f "${RESINKIT_API_VENV_DIR}/bin/activate" ]; then
    echo "[RESINKIT] Resinkit API venv found at ${RESINKIT_API_VENV_DIR}, starting service..."
    mkdir -p "$(dirname "$RESINKIT_API_LOG_FILE")"
    source "${RESINKIT_API_VENV_DIR}/bin/activate"
    nohup uvicorn resinkit_api.main:app --host 0.0.0.0 --port "$RESINKIT_API_SERVICE_PORT" >"$RESINKIT_API_LOG_FILE" 2>&1 &
else
    echo "[RESINKIT] Resinkit API venv not found at ${RESINKIT_API_VENV_DIR}, starting service..."
    exit 1
fi

echo "----------------------------------------"
echo "Resinkit API started"
echo "----------------------------------------"

if [ "$RUNNING_TAIL_F" = true ]; then
    echo "[RESINKIT] Running foreground"
    tail -f /dev/null
fi
