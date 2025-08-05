#!/bin/bash
# shellcheck disable=SC1091,SC2155

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop}"
    echo "  start       Start Flink cluster and SQL Gateway services"
    echo "  stop        Stop Flink cluster and SQL Gateway services"
    echo ""
    exit 1
}

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
        "/opt/flink/bin/sql-gateway.sh" stop
        sleep 3
        
        # Force kill if still running
        local remaining_gateway_pids
        remaining_gateway_pids=$(pgrep -f "org.apache.flink.table.gateway.SqlGateway" || true)
        if [[ -n "$remaining_gateway_pids" ]]; then
            echo "[RESINKIT] Force killing remaining Flink SQL Gateway processes..."
            for pid in $remaining_gateway_pids; do
                kill -9 "$pid"
            done
        fi
    else
        echo "[RESINKIT] Flink SQL Gateway is not running"
    fi

    # Stop Flink cluster
    if is_flink_running; then
        echo "[RESINKIT] Stopping Flink cluster..."
        "/opt/flink/bin/stop-cluster.sh"
        sleep 5
        
        # Force kill remaining processes if any
        local remaining_tm_pids
        remaining_tm_pids=$(pgrep -f "org.apache.flink.runtime.taskexecutor.TaskManagerRunner" || true)
        if [[ -n "$remaining_tm_pids" ]]; then
            echo "[RESINKIT] Force killing remaining TaskManager processes..."
            for pid in $remaining_tm_pids; do
                kill -9 "$pid"
            done
        fi
        
        local remaining_jm_pids
        remaining_jm_pids=$(pgrep -f "org.apache.flink.runtime.entrypoint.StandaloneSessionClusterEntrypoint" || true)
        if [[ -n "$remaining_jm_pids" ]]; then
            echo "[RESINKIT] Force killing remaining JobManager processes..."
            for pid in $remaining_jm_pids; do
                kill -9 "$pid"
            done
        fi
    else
        echo "[RESINKIT] Flink cluster is not running"
    fi
    
    echo "[RESINKIT] Flink cluster and SQL gateway stopped"
}

# Function to start Flink cluster and SQL gateway
start_flink() {
    echo "[RESINKIT] Starting Flink cluster and SQL gateway..."
    
    # Check if services are already running
    if is_flink_running && is_flink_sql_gateway_running; then
        echo "[RESINKIT] Flink cluster and SQL Gateway are already running"
        return 0
    fi

    # Ensure HADOOP_CLASSPATH is set for Iceberg integration (following official Iceberg guide)
    if [[ -d "/opt/hadoop" ]] && [[ -f "/opt/hadoop/bin/hadoop" ]]; then
        export HADOOP_CLASSPATH=$(/opt/hadoop/bin/hadoop classpath)
        echo "[RESINKIT] HADOOP_CLASSPATH set for Iceberg integration"
    else
        echo "[RESINKIT] Warning: Hadoop not found or HADOOP_HOME not set, Iceberg integration may not work properly"
    fi

    # Start Flink cluster
    if ! is_flink_running; then
        echo "[RESINKIT] Starting Flink cluster..."
        "/opt/flink/bin/start-cluster.sh"
        
        # Wait for cluster to start
        echo "[RESINKIT] Waiting for Flink cluster to start..."
        sleep 5
        
        # Verify Flink cluster started
        if ! is_flink_running; then
            echo "[RESINKIT] Error: Failed to start Flink cluster"
            exit 1
        fi
        echo "[RESINKIT] Flink cluster started successfully"
    else
        echo "[RESINKIT] Flink cluster is already running"
    fi
    
    # Start SQL Gateway
    if ! is_flink_sql_gateway_running; then
        echo "[RESINKIT] Starting Flink SQL Gateway..."
        "/opt/flink/bin/sql-gateway.sh" start -Dsql-gateway.endpoint.rest.address=localhost
        
        # Wait for SQL Gateway to start
        echo "[RESINKIT] Waiting for Flink SQL Gateway to start..."
        sleep 5
        
        # Verify SQL Gateway started
        if ! is_flink_sql_gateway_running; then
            echo "[RESINKIT] Error: Failed to start Flink SQL Gateway"
            exit 1
        fi
        echo "[RESINKIT] Flink SQL Gateway started successfully"
    else
        echo "[RESINKIT] Flink SQL Gateway is already running"
    fi
    
    echo "[RESINKIT] Flink cluster and SQL Gateway services are running"
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
        start_flink
        ;;
    stop)
        stop_flink
        ;;
    *)
        echo "Error: Unknown command '$command'"
        usage
        ;;
    esac
}

# Run the main function with all arguments
main "$@"