#!/bin/sh

# Ensure required environment variables are set
if [ -z "${KAFKA_HOME}" ] || [ -z "${FLINK_HOME}" ] || [ -z "${RESINKIT_API_PATH}" ]; then
    # shellcheck disable=SC1091
    . /etc/environment
fi

# Start Kafka
"${KAFKA_HOME}/bin/zookeeper-server-start.sh" "${KAFKA_HOME}/config/zookeeper.properties" &
"${KAFKA_HOME}/bin/kafka-server-start.sh" "${KAFKA_HOME}/config/server.properties" &

# Start Flink session cluster & SQL gateway
"${FLINK_HOME}/bin/start-cluster.sh"
"${FLINK_HOME}/bin/sql-gateway.sh" start -Dsql-gateway.endpoint.rest.address=localhost

# Start Resinkit API, using gunicorn
echo "starting resinkit at: ${RESINKIT_API_PATH}"
cd "$RESINKIT_API_PATH" && ./scripts/install.sh

echo "----------------------------------------"
echo "Resinkit API started"
echo "----------------------------------------"
