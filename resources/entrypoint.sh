#!/bin/bash
# Usage:
# 1. Set RESINKIT_API_GITHUB_TOKEN to use the repository version of the Resinkit API
# 2. Set FORCE_RESTART=true to restart the services

# shellcheck disable=SC1091
. /etc/environment.seed
. /etc/environment

# Function to check if Kafka is running
is_kafka_running() {
    # Check if Kafka process is running
    if pgrep -f "kafka.Kafka" >/dev/null; then
        return 0 # Kafka is running
    else
        return 1 # Kafka is not running
    fi
}

# Function to check if Zookeeper is running
is_zookeeper_running() {
    # Check if Zookeeper process is running
    if pgrep -f "org.apache.zookeeper.server.quorum.QuorumPeerMain" >/dev/null; then
        return 0 # Zookeeper is running
    else
        return 1 # Zookeeper is not running
    fi
}

# Function to stop Kafka and Zookeeper
stop_kafka_zookeeper() {
    echo "[RESINKIT] Stopping Kafka and Zookeeper..."

    # Stop Kafka first
    if is_kafka_running; then
        echo "[RESINKIT] Stopping Kafka..."
        "${KAFKA_HOME}/bin/kafka-server-stop.sh"
        # Wait for Kafka to stop
        sleep 5
    fi

    # Stop Zookeeper
    if is_zookeeper_running; then
        echo "[RESINKIT] Stopping Zookeeper..."
        "${KAFKA_HOME}/bin/zookeeper-server-stop.sh"
        # Wait for Zookeeper to stop
        sleep 5
    fi
}

# Function to start Kafka and Zookeeper
start_kafka_zookeeper() {
    echo "[RESINKIT] Starting Zookeeper and Kafka..."
    "${KAFKA_HOME}/bin/zookeeper-server-start.sh" "${KAFKA_HOME}/config/zookeeper.properties" &
    sleep 10 # Wait for Zookeeper to start before starting Kafka
    "${KAFKA_HOME}/bin/kafka-server-start.sh" "${KAFKA_HOME}/config/server.properties" &
}

# Check if Kafka is already running and handle accordingly
if is_kafka_running || is_zookeeper_running; then
    echo "[RESINKIT] Kafka/Zookeeper is already running"

    if [ "$FORCE_RESTART" = true ]; then
        echo "[RESINKIT] FORCE_RESTART is true, restarting Kafka and Zookeeper..."
        stop_kafka_zookeeper
        start_kafka_zookeeper
    else
        echo "[RESINKIT] Skipping Kafka/Zookeeper startup (already running). Set FORCE_RESTART=true to restart."
    fi
else
    echo "[RESINKIT] Kafka/Zookeeper not running, starting services..."
    start_kafka_zookeeper
fi

# Function to check if Flink cluster is running
is_flink_running() {
    # Check if Flink TaskManager and JobManager processes are running
    if pgrep -f "org.apache.flink.runtime.taskexecutor.TaskManagerRunner" >/dev/null &&
        pgrep -f "org.apache.flink.runtime.entrypoint.StandaloneSessionClusterEntrypoint" >/dev/null; then
        return 0 # Flink is running
    else
        return 1 # Flink is not running
    fi
}

# Function to check if Flink SQL Gateway is running
is_flink_sql_gateway_running() {
    # Check if Flink SQL Gateway process is running
    if pgrep -f "org.apache.flink.table.gateway.SqlGateway" >/dev/null; then
        return 0 # Flink SQL Gateway is running
    else
        return 1 # Flink SQL Gateway is not running
    fi
}

# Function to stop Flink cluster and SQL gateway
stop_flink() {
    echo "[RESINKIT] Stopping Flink cluster and SQL gateway..."

    # Stop SQL Gateway first
    if is_flink_sql_gateway_running; then
        echo "[RESINKIT] Stopping Flink SQL Gateway..."
        "${FLINK_HOME}/bin/sql-gateway.sh" stop
        sleep 3
        pkill -f "org.apache.flink.table.gateway.SqlGateway" || echo "[RESINKIT] Flink SQL Gateway already stopped"
    fi

    # Stop Flink cluster
    if is_flink_running; then
        echo "[RESINKIT] Stopping Flink cluster..."
        "${FLINK_HOME}/bin/stop-cluster.sh"
        sleep 5
        pkill -f "org.apache.flink.runtime.taskexecutor.TaskManagerRunner" || echo "[RESINKIT] Flink TaskManagerRunner already stopped"
        pkill -f "org.apache.flink.runtime.entrypoint.StandaloneSessionClusterEntrypoint" || echo "[RESINKIT] Flink StandaloneSessionClusterEntrypoint already stopped"
    fi
}

# Function to start Flink cluster and SQL gateway
start_flink() {
    echo "[RESINKIT] Starting Flink cluster and SQL gateway..."

    # Ensure HADOOP_CLASSPATH is set for Iceberg integration (following official Iceberg guide)
    if [ -f "$HADOOP_HOME/bin/hadoop" ]; then
        export HADOOP_CLASSPATH=$($HADOOP_HOME/bin/hadoop classpath)
        echo "[RESINKIT] HADOOP_CLASSPATH set for Iceberg: $HADOOP_CLASSPATH"
    else
        echo "[RESINKIT] Warning: Hadoop not found, Iceberg integration may not work properly"
    fi

    "${FLINK_HOME}/bin/start-cluster.sh"
    sleep 5 # Wait for cluster to start before starting SQL gateway
    "${FLINK_HOME}/bin/sql-gateway.sh" start -Dsql-gateway.endpoint.rest.address=localhost
}

# Check if Flink is already running and handle accordingly
if is_flink_running || is_flink_sql_gateway_running; then
    echo "[RESINKIT] Flink cluster/SQL Gateway is already running"

    if [ "$FORCE_RESTART" = true ]; then
        echo "[RESINKIT] FORCE_RESTART is true, restarting Flink cluster and SQL gateway..."
        stop_flink
        start_flink
    else
        echo "[RESINKIT] Skipping Flink startup (already running). Set FORCE_RESTART=true to restart."
    fi
else
    echo "[RESINKIT] Flink cluster/SQL Gateway not running, starting services..."
    start_flink
fi

# Function to check if genai-toolbox is running
is_genai_toolbox_running() {
    # Check if genai-toolbox process is running
    if pgrep -f "toolbox" >/dev/null; then
        return 0 # genai-toolbox is running
    else
        return 1 # genai-toolbox is not running
    fi
}

# Function to stop genai-toolbox
stop_genai_toolbox() {
    echo "[RESINKIT] Stopping genai-toolbox..."
    pkill -f "toolbox" || echo "[RESINKIT] genai-toolbox already stopped"
    sleep 2
}

# Function to start genai-toolbox
start_genai_toolbox() {
    echo "[RESINKIT] Starting genai-toolbox..."

    # Check if toolbox binary exists
    if [ ! -f "${GENAI_TOOLBOX_BIN}" ]; then
        echo "[RESINKIT] Warning: genai-toolbox not found at ${GENAI_TOOLBOX_BIN}, skipping startup"
        return 0
    fi

    # Start genai-toolbox in the background
    cd ${GENAI_TOOLBOX_DIR} || return 1
    nohup ${GENAI_TOOLBOX_BIN} --tools-file ${GENAI_TOOLBOX_TOOLS_YAML} --address 0.0.0.0 >${GENAI_TOOLBOX_DIR}/genai-toolbox.log 2>&1 &
    echo "[RESINKIT] genai-toolbox started (logs at ${GENAI_TOOLBOX_DIR}/genai-toolbox.log)"
}

# Check if genai-toolbox is already running and handle accordingly
if is_genai_toolbox_running; then
    echo "[RESINKIT] genai-toolbox is already running"

    if [ "$FORCE_RESTART" = true ]; then
        echo "[RESINKIT] FORCE_RESTART is true, restarting genai-toolbox..."
        stop_genai_toolbox
        start_genai_toolbox
    else
        echo "[RESINKIT] Skipping genai-toolbox startup (already running). Set FORCE_RESTART=true to restart."
    fi
else
    echo "[RESINKIT] genai-toolbox not running, starting service..."
    start_genai_toolbox
fi

# Start Resinkit API service using the dedicated entrypoint script
echo "[RESINKIT] Starting Resinkit API service..."

if [ "$FORCE_RESTART" = true ]; then
    echo "[RESINKIT] FORCE_RESTART is true, stopping service first..."
    $RESINKIT_API_PATH/resinkit-api-entrypoint.sh stop
fi

echo "[RESINKIT] Starting Resinkit API service..."
$RESINKIT_API_PATH/resinkit-api-entrypoint.sh start

echo "----------------------------------------"
echo "Resinkit API started"
echo "----------------------------------------"

if [ "$RUNNING_TAIL_F" = true ]; then
    echo "[RESINKIT] Running foreground"
    tail -f /dev/null
fi
