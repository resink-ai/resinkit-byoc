#!/bin/bash

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop|status}"
    echo "  start       Start the jupyterlab service"
    echo "  stop        Stop the jupyterlab service"
    echo "  status      Check status of Jupyter service"
    exit 1
}

JUPYTER_PORT="${JUPYTER_PORT:-8888}"
JUPYTER_WORKSPACE_DIR="/home/resinkit/resinkit_sample_project/notebooks"

# Function to start the service
start_service() {

    # Check if service is already running
    if pgrep -f "jupyter notebook" >/dev/null; then
        echo "[RESINKIT] Jupyter service is already running"
        return 0
    fi

    
    # Start the service
    echo "[RESINKIT] Starting jupyter service..."

    
    mkdir -p "$JUPYTER_WORKSPACE_DIR"

    cd /home/resinkit/resinkit_sample_project
    nohup /home/resinkit/.local/bin/uv run --directory /home/resinkit/resinkit_sample_project jupyter lab \
        --notebook-dir="$JUPYTER_WORKSPACE_DIR" \
        --ip=0.0.0.0 \
        --port=$JUPYTER_PORT \
        --no-browser \
        --NotebookApp.terminals_enabled=False \
        --NotebookApp.token="" /dev/null 2>&1 &

    # Get the PID and save it
    local pid=$!
    echo "[RESINKIT] Jupyter service started with PID: $pid"
    echo "[RESINKIT] Logs are being written to: /dev/null"

}

# Function to stop the service
stop_service() {
    echo "[RESINKIT] Stopping jupyter service..."

    # Find and kill the jupyter process
    local pids=$(pgrep -f "jupyter lab" || true)

    if [[ -z "$pids" ]]; then
        echo "[RESINKIT] No jupyter service found running"
        return 0
    fi

    # Kill the processes
    for pid in $pids; do
        echo "[RESINKIT] Killing process $pid"
        kill "$pid"
    done

    # Wait a moment and check if processes are still running
    sleep 2
    local remaining_pids=$(pgrep -f "jupyter lab" || true)

    if [[ -n "$remaining_pids" ]]; then
        echo "[RESINKIT] Force killing remaining processes..."
        for pid in $remaining_pids; do
            kill -9 "$pid"
        done
    fi

    echo "[RESINKIT] Jupyter service stopped"
}

# Function to check status of Jupyter service
status_service() {
    echo "[RESINKIT] Checking Jupyter service status..."
    
    # Check if Jupyter is running
    local pids=$(pgrep -f "jupyter lab" || true)
    
    if [[ -n "$pids" ]]; then
        echo "[RESINKIT] ✅ Jupyter service is running"
        echo "[RESINKIT]   Jupyter PIDs: $pids"
        
        # Test Jupyter accessibility
        if curl -s --connect-timeout 5 http://localhost:$JUPYTER_PORT >/dev/null 2>&1; then
            echo "[RESINKIT] ✅ Jupyter accessible at http://localhost:$JUPYTER_PORT"
        else
            echo "[RESINKIT] ❌ Jupyter not accessible at http://localhost:$JUPYTER_PORT"
        fi
        
        # Check workspace directory
        if [[ -d "$JUPYTER_WORKSPACE_DIR" ]]; then
            echo "[RESINKIT] ✅ Jupyter workspace directory exists: $JUPYTER_WORKSPACE_DIR"
        else
            echo "[RESINKIT] ❌ Jupyter workspace directory missing: $JUPYTER_WORKSPACE_DIR"
        fi
    else
        echo "[RESINKIT] ❌ Jupyter service is not running"
    fi
}

# Main script logic
main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi

    local command=$1

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
