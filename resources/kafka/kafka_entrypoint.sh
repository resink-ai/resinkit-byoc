#!/bin/bash

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop|status}"
    echo "  start       Start Kafka and Zookeeper services"
    echo "  stop        Stop Kafka and Zookeeper services"
    echo "  status      Check status of Kafka and Zookeeper services"
    echo ""
    echo "Environment variables:"
    echo "  KAFKA_HOME    Path to Kafka installation (default: /opt/kafka)"
    exit 1
}

export KAFKA_HOME="${KAFKA_HOME:-/opt/kafka}"

# Function to check required environment variables
check_env_vars() {
    local required_vars=("KAFKA_HOME")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo "Error: Environment variable $var is not set"
            echo "Please check the environment, example:"
            echo "  KAFKA_HOME=/opt/kafka"
            exit 1
        fi
    done

    if [[ ! -f "$KAFKA_HOME/bin/kafka-server-start.sh" ]]; then
        echo "Error: Kafka scripts not found at $KAFKA_HOME/bin/"
        exit 1
    fi
}

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
        
        # Force kill if still running
        local remaining_kafka_pids
        remaining_kafka_pids=$(pgrep -f "kafka.Kafka" || true)
        if [[ -n "$remaining_kafka_pids" ]]; then
            echo "[RESINKIT] Force killing remaining Kafka processes..."
            for pid in $remaining_kafka_pids; do
                kill -9 "$pid"
            done
        fi
    else
        echo "[RESINKIT] Kafka is not running"
    fi

    # Stop Zookeeper
    if is_zookeeper_running; then
        echo "[RESINKIT] Stopping Zookeeper..."
        "${KAFKA_HOME}/bin/zookeeper-server-stop.sh"
        # Wait for Zookeeper to stop
        sleep 5
        
        # Force kill if still running
        local remaining_zk_pids
        remaining_zk_pids=$(pgrep -f "org.apache.zookeeper.server.quorum.QuorumPeerMain" || true)
        if [[ -n "$remaining_zk_pids" ]]; then
            echo "[RESINKIT] Force killing remaining Zookeeper processes..."
            for pid in $remaining_zk_pids; do
                kill -9 "$pid"
            done
        fi
    else
        echo "[RESINKIT] Zookeeper is not running"
    fi
    
    echo "[RESINKIT] Kafka and Zookeeper stopped"
}

# Function to start Kafka and Zookeeper
start_kafka_zookeeper() {
    echo "[RESINKIT] Starting Zookeeper and Kafka..."
    
    # Check if services are already running
    if is_kafka_running && is_zookeeper_running; then
        echo "[RESINKIT] Kafka and Zookeeper are already running"
        return 0
    fi
    
    # Start Zookeeper first
    if ! is_zookeeper_running; then
        echo "[RESINKIT] Starting Zookeeper..."
        nohup "${KAFKA_HOME}/bin/zookeeper-server-start.sh" "${KAFKA_HOME}/config/zookeeper.properties" >/dev/null 2>&1 &
        
        # Wait for Zookeeper to start
        echo "[RESINKIT] Waiting for Zookeeper to start..."
        sleep 10
        
        # Verify Zookeeper started
        if ! is_zookeeper_running; then
            echo "[RESINKIT] Error: Failed to start Zookeeper"
            exit 1
        fi
        echo "[RESINKIT] Zookeeper started successfully"
    else
        echo "[RESINKIT] Zookeeper is already running"
    fi
    
    # Start Kafka
    if ! is_kafka_running; then
        echo "[RESINKIT] Starting Kafka..."
        nohup "${KAFKA_HOME}/bin/kafka-server-start.sh" "${KAFKA_HOME}/config/server.properties" >/dev/null 2>&1 &
        
        # Wait for Kafka to start
        echo "[RESINKIT] Waiting for Kafka to start..."
        sleep 10
        
        # Verify Kafka started
        if ! is_kafka_running; then
            echo "[RESINKIT] Error: Failed to start Kafka"
            exit 1
        fi
        echo "[RESINKIT] Kafka started successfully"
    else
        echo "[RESINKIT] Kafka is already running"
    fi
    
    echo "[RESINKIT] Kafka and Zookeeper services are running"
}

# Function to check status of Kafka and Zookeeper services
status_kafka_zookeeper() {
    echo "[RESINKIT] Checking Kafka and Zookeeper services status..."
    
    # Check Zookeeper status
    if is_zookeeper_running; then
        echo "[RESINKIT] ✅ Zookeeper is running"
        local zk_pids=$(pgrep -f "org.apache.zookeeper.server.quorum.QuorumPeerMain" || true)
        echo "[RESINKIT]   Zookeeper PIDs: $zk_pids"
    else
        echo "[RESINKIT] ❌ Zookeeper is not running"
    fi
    
    # Check Kafka status
    if is_kafka_running; then
        echo "[RESINKIT] ✅ Kafka is running"
        local kafka_pids=$(pgrep -f "kafka.Kafka" || true)
        echo "[RESINKIT]   Kafka PIDs: $kafka_pids"
        
        # Test Kafka connectivity if kcat is available
        if command -v kcat >/dev/null 2>&1; then
            echo "[RESINKIT]   Testing Kafka connectivity..."
            if timeout 5 kcat -L -b localhost:9092 >/dev/null 2>&1; then
                echo "[RESINKIT] ✅ Kafka broker accessible at localhost:9092"
            else
                echo "[RESINKIT] ❌ Kafka broker not accessible at localhost:9092"
            fi
        fi
    else
        echo "[RESINKIT] ❌ Kafka is not running"
    fi
}

# Function to check status with environment validation
status_service() {
    echo "[RESINKIT] Checking environment variables..."
    check_env_vars
    
    status_kafka_zookeeper
}

# Function to start the services
start_service() {
    echo "[RESINKIT] Checking environment variables..."
    check_env_vars
    
    start_kafka_zookeeper
}

# Function to stop the services
stop_service() {
    echo "[RESINKIT] Checking environment variables..."
    check_env_vars
    
    stop_kafka_zookeeper
}

# Main script logic
main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi

    local command=$1

    # Check for invalid arguments
    if [[ $# -gt 1 ]]; then
        usage
    fi

    case "$command" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    status)
        status_service
        ;;
    *)
        echo "Error: Unknown command '$command'"
        usage
        ;;
    esac
}

# Run the main function with all arguments
main "$@"