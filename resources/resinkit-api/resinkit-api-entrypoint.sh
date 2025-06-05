#!/bin/bash

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop} [--repo]"
    echo "  start       Start the resinkit API service"
    echo "  start --repo Start the service and install from local repo"
    echo "  stop        Stop the resinkit API service"
    exit 1
}

# Function to check required environment variables
check_env_vars() {
    local required_vars=("RESINKIT_API_VENV_DIR" "RESINKIT_API_SERVICE_PORT" "RESINKIT_API_LOG_FILE")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo "Error: Environment variable $var is not set"
            exit 1
        fi
    done
}

install_uv_venv_if_not_exists() {
    # Install uv if not already installed
    if ! command -v uv &>/dev/null; then
        echo "[QQQ] Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        # Add uv to PATH for current session
        source "$HOME/.local/bin/env"
    fi

    # Create virtual environment using uv if it doesn't exist
    if [[ ! -f "$RESINKIT_API_VENV_DIR/bin/activate" ]]; then
        echo "[QQQ] Creating virtual environment with uv..."
        uv venv "$RESINKIT_API_VENV_DIR" --python 3.12
    fi
}

# Function to install dependencies
install_dependencies() {
    local use_repo=$1

    echo "[QQQ] Installing dependencies..."

    if [[ "$use_repo" == "true" ]]; then
        echo "[QQQ] Installing from local repository..."
        uv pip install -e . --python "$RESINKIT_API_VENV_DIR/bin/python"
    else
        echo "[QQQ] Installing from PyPI..."
        uv pip install uvicorn resinkit-api-python -U --python "$RESINKIT_API_VENV_DIR/bin/python"
    fi
}

# Function to start the service
start_service() {
    local use_repo=$1

    # Check if service is already running
    if pgrep -f "uvicorn resinkit_api.main:app" >/dev/null; then
        echo "[QQQ] Resinkit API service is already running"
        return 0
    fi

    echo "[QQQ] Checking environment variables..."
    check_env_vars

    cd "$RESINKIT_API_PATH"

    echo "[QQQ] Installing uv if not exists"
    install_uv_venv_if_not_exists

    echo "[QQQ] Activating virtual environment..."
    source "$RESINKIT_API_VENV_DIR/bin/activate"

    echo "[QQQ] Installing dependencies if needed"
    install_dependencies "$use_repo"

    # Start the service
    echo "[QQQ] Starting resinkit_api service..."
    mkdir -p "$(dirname "$RESINKIT_API_LOG_FILE")"

    nohup uvicorn resinkit_api.main:app --host 0.0.0.0 --port "$RESINKIT_API_SERVICE_PORT" >"$RESINKIT_API_LOG_FILE" 2>&1 &

    # Get the PID and save it
    local pid=$!
    echo "[QQQ] Resinkit API service started with PID: $pid"
    echo "[QQQ] Logs are being written to: $RESINKIT_API_LOG_FILE"

}

# Function to stop the service
stop_service() {
    echo "[QQQ] Stopping resinkit_api service..."

    # Find and kill the uvicorn process
    local pids=$(pgrep -f "uvicorn resinkit_api.main:app" || true)

    if [[ -z "$pids" ]]; then
        echo "[QQQ] No resinkit_api service found running"
        return 0
    fi

    # Kill the processes
    for pid in $pids; do
        echo "[QQQ] Killing process $pid"
        kill "$pid"
    done

    # Wait a moment and check if processes are still running
    sleep 2
    local remaining_pids=$(pgrep -f "uvicorn resinkit_api.main:app" || true)

    if [[ -n "$remaining_pids" ]]; then
        echo "[QQQ] Force killing remaining processes..."
        for pid in $remaining_pids; do
            kill -9 "$pid"
        done
    fi

    echo "[QQQ] Resinkit API service stopped"
}

# Main script logic
main() {
    if [[ $# -eq 0 ]]; then
        usage
    fi

    local command=$1
    local use_repo=false

    # Check for --repo flag
    if [[ $# -eq 2 && "$2" == "--repo" ]]; then
        use_repo=true
    elif [[ $# -gt 2 || ($# -eq 2 && "$2" != "--repo") ]]; then
        usage
    fi

    case "$command" in
    start)
        start_service "$use_repo"
        ;;
    stop)
        if [[ "$use_repo" == "true" ]]; then
            echo "Warning: --repo flag is ignored for stop command"
        fi
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
