#!/bin/bash

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop}"
    echo "  start       Start the resinkit API service"
    echo "  stop        Stop the resinkit API service"
    echo ""
    echo "Environment variables:"
    echo "  RESINKIT_API_GITHUB_TOKEN  If set, install from local repository instead of PyPI"
    exit 1
}

export RESINKIT_API_PATH="${RESINKIT_API_PATH:-/opt/resinkit/api}"
export RESINKIT_API_LOG_FILE="${RESINKIT_API_LOG_FILE:-/opt/resinkit/api/resinkit_api.log}"
export RESINKIT_API_SERVICE_PORT="${RESINKIT_API_SERVICE_PORT:-8602}"

export INSTALLER_NO_MODIFY_PATH=1
export UV_CACHE_DIR="/home/resinkit/.uv/cache"
export UV_CONFIG_DIR="/home/resinkit/.uv/config"
export UV_DATA_DIR="/home/resinkit/.uv/data"
mkdir -p "$UV_CACHE_DIR" "$UV_CONFIG_DIR" "$UV_DATA_DIR"

UV_BIN="/home/resinkit/.local/bin/uv"
if [ ! -f "$UV_BIN" ]; then
    echo "[RESINKIT] UV not installed"
    exit 1
fi

# Function to install dependencies
install_dependencies() {
    echo "[RESINKIT] Installing dependencies..."

    if [[ -n "$RESINKIT_API_GITHUB_TOKEN" ]]; then
        echo "[RESINKIT] Installing from local repository..."
        $UV_BIN --directory "$RESINKIT_API_PATH" --python 3.12 sync
    else
        echo "[RESINKIT] Installing from PyPI..."
        $UV_BIN --directory "$RESINKIT_API_PATH" --python 3.12 pip install uvicorn resinkit-api-python -U
    fi
}

# Function to start the service
start_service() {
    # Check if service is already running
    if pgrep -f "uvicorn resinkit_api.main:app" >/dev/null; then
        echo "[RESINKIT] Resinkit API service is already running"
        return 0
    fi


    cd "$RESINKIT_API_PATH"

    echo "[RESINKIT] Installing uv if not exists"
    install_uv_venv_if_not_exists

    echo "[RESINKIT] Activating virtual environment..."
    source "$RESINKIT_API_VENV_DIR/bin/activate"

    echo "[RESINKIT] Installing dependencies if needed"
    install_dependencies

    # Start the service
    echo "[RESINKIT] Starting resinkit_api service..."
    mkdir -p "$(dirname "$RESINKIT_API_LOG_FILE")"

    nohup $UV_BIN --directory "$RESINKIT_API_PATH" --python 3.12 run uvicorn resinkit_api.main:app --host 0.0.0.0 --port "$RESINKIT_API_SERVICE_PORT" >"$RESINKIT_API_LOG_FILE" 2>&1 &

    # Get the PID and save it
    local pid=$!
    echo "[RESINKIT] Resinkit API service started with PID: $pid"
    echo "[RESINKIT] Logs are being written to: $RESINKIT_API_LOG_FILE"

}

# Function to stop the service
stop_service() {
    echo "[RESINKIT] Stopping resinkit_api service..."

    # Find and kill the uvicorn process
    local pids=$(pgrep -f "uvicorn resinkit_api.main:app" || true)

    if [[ -z "$pids" ]]; then
        echo "[RESINKIT] No resinkit_api service found running"
        return 0
    fi

    # Kill the processes
    for pid in $pids; do
        echo "[RESINKIT] Killing process $pid"
        kill "$pid"
    done

    # Wait a moment and check if processes are still running
    sleep 2
    local remaining_pids=$(pgrep -f "uvicorn resinkit_api.main:app" || true)

    if [[ -n "$remaining_pids" ]]; then
        echo "[RESINKIT] Force killing remaining processes..."
        for pid in $remaining_pids; do
            kill -9 "$pid"
        done
    fi

    echo "[RESINKIT] Resinkit API service stopped"
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
    *)
        echo "Error: Unknown command '$command'"
        usage
        ;;
    esac
}

# Run the main function with all arguments
main "$@"
