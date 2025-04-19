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

test_flink() {
    # test flink & flink sql gateway
    curl -s http://localhost:8083/info
    curl -s http://localhost:8081/config
    curl -H "Authorization: pat_xyz" http://127.0.0.1:8602/api/v1/pat/validate

    # from outside the container
    curl -s http://localhost:8080/flink_sql_gateway/info
    curl -s http://localhost:8080/flink_ui/config
}

# Start Resinkit API, using gunicorn
echo "starting resinkit at: ${RESINKIT_API_PATH}"
cd "$RESINKIT_API_PATH" && ./scripts/install.sh

echo "done"
