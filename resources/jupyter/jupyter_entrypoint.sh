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

export INSTALLER_NO_MODIFY_PATH=1
export UV_CACHE_DIR="/home/jupyter/.uv/cache"
export UV_CONFIG_DIR="/home/jupyter/.uv/config"
export UV_DATA_DIR="/home/jupyter/.uv/data"
export JUPYTER_LOG_FILE="/home/jupyter/logs/jupyter.log"
mkdir -p "$UV_CACHE_DIR" "$UV_CONFIG_DIR" "$UV_DATA_DIR"

VENV_DIR="/home/jupyter/workspace/resinkit_sample_project/.venv"

install_uv_venv_if_not_exists() {
    # Install uv if not already installed
    if ! command -v uv &>/dev/null; then
        echo "[RESINKIT] Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh || true
        # Add uv to PATH for current session
        export PATH="/home/jupyter/.local/bin:$PATH"
        # source "$RESINKIT_ROLE_HOME/.local/bin/env"
        echo "[RESINKIT] UV_HOME: /home/jupyter/.local/bin"
        echo "[RESINKIT] UV_CACHE_DIR: $UV_CACHE_DIR"
        echo "[RESINKIT] UV_CONFIG_DIR: $UV_CONFIG_DIR"
        echo "[RESINKIT] UV_DATA_DIR: $UV_DATA_DIR"
        echo "[RESINKIT] PATH: $PATH"
        echo "[RESINKIT] uv --version: $(uv --version)"
    fi

    # Create virtual environment using uv if it doesn't exist
    if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
        echo "[RESINKIT] Creating virtual environment for jupyter at $VENV_DIR with uv..."
        echo "[RESINKIT] CMD: uv venv $VENV_DIR --python 3.12"
        /home/jupyter/.local/bin/uv venv "$VENV_DIR" --python 3.12
    fi
}

# Function to install dependencies
activate_venv_and_install_dependencies() {
    echo "[RESINKIT] Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo "[RESINKIT] Installing dependencies..."
    cd "/home/jupyter/workspace/resinkit_sample_project"
    /home/jupyter/.local/bin/uv sync --python "$VENV_DIR/bin/python3"
}

# Function to start the service
start_service() {

    # Check if service is already running
    if pgrep -f "jupyter notebook" >/dev/null; then
        echo "[RESINKIT] Jupyter service is already running"
        return 0
    fi

    echo "[RESINKIT] Installing uv if not exists"
    install_uv_venv_if_not_exists

    echo "[RESINKIT] Activating virtual environment and installing dependencies..."
    activate_venv_and_install_dependencies

    # Start the service
    echo "[RESINKIT] Starting jupyter service..."
    mkdir -p "$(dirname "$JUPYTER_LOG_FILE")"

    jupyter_workspace_dir="/home/jupyter/workspace/resinkit_sample_project/notebooks"
    mkdir -p "$jupyter_workspace_dir"

    nohup /home/jupyter/.local/bin/uv run --python "$VENV_DIR/bin/python3" jupyter lab \
        --notebook-dir="$jupyter_workspace_dir" \
        --ip=0.0.0.0 \
        --port=8888 \
        --no-browser \
        --NotebookApp.terminals_enabled=False \
        --NotebookApp.token="" >"$JUPYTER_LOG_FILE" 2>&1 &

    # Get the PID and save it
    local pid=$!
    echo "[RESINKIT] Jupyter service started with PID: $pid"
    echo "[RESINKIT] Logs are being written to: $JUPYTER_LOG_FILE"

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
