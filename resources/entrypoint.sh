#!/bin/sh

# Ensure required environment variables are set
if [ -z "${KAFKA_HOME}" ] || [ -z "${FLINK_HOME}" ] || [ -z "${RESINKIT_JAR_PATH}" ]; then
    # shellcheck source=/etc/environment
    . /etc/environment
fi

# Start Kafka
"${KAFKA_HOME}/bin/zookeeper-server-start.sh" "${KAFKA_HOME}/config/zookeeper.properties" &
"${KAFKA_HOME}/bin/kafka-server-start.sh" "${KAFKA_HOME}/config/server.properties" &

# Start Flink session cluster & SQL gateway
"${FLINK_HOME}/bin/start-cluster.sh"
"${FLINK_HOME}/bin/sql-gateway.sh" start -Dsql-gateway.endpoint.rest.address=localhost

# Start Resinkit API
echo "starting resinkit at: ${RESINKIT_JAR_PATH}"
exec java -jar "${RESINKIT_JAR_PATH}"
