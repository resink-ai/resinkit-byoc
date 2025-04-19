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

# test flink & flink sql gateway
curl -s http://localhost:8083/info
# from outside the container
curl -s http://localhost:8080/flink_sql_gateway/info
curl -s http://localhost:8081/config

# Start Resinkit API, using gunicorn
echo "starting resinkit at: ${RESINKIT_API_PATH}"
cd "$RESINKIT_API_PATH" && ./scripts/install.sh

if [ -f /.dockerenv ]; then
    echo "[RESINKIT] Running inside Docker"
    nginx || nginx -s reload
else
    echo "[RESINKIT] Not running inside Docker"
    systemctl enable nginx
    systemctl start nginx
fi

if [ "$1" = "-f" ] || [ "$1" = "--foreground" ]; then
    tail -f /dev/null
fi

echo "done"
