#!/bin/bash

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop}"
    echo "  start       Start the jupyterlab service"
    echo "  stop        Stop the jupyterlab service"
    exit 1
}

RESINKIT_ROLE="resinkit"

# Function to start the service
start_service() {

    # Check if service is already running
    if pgrep -f "jupyter notebook" >/dev/null; then
        echo "[RESINKIT] Jupyter service is already running"
        return 0
    fi

    
    # Start the service
    echo "[RESINKIT] Starting jupyter service..."

    jupyter_workspace_dir="/home/$RESINKIT_ROLE/resinkit_sample_project/notebooks"
    mkdir -p "$jupyter_workspace_dir"

    cd /home/$RESINKIT_ROLE/resinkit_sample_project
    nohup /home/$RESINKIT_ROLE/.local/bin/uv run --directory /home/$RESINKIT_ROLE/resinkit_sample_project jupyter lab \
        --notebook-dir="$jupyter_workspace_dir" \
        --ip=0.0.0.0 \
        --port=8888 \
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
    *)
        echo "Error: Unknown command '$command'"
        usage
        ;;
    esac
}

# Run the main function with all arguments
main "$@"
