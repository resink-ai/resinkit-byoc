#!/bin/bash

# Exit on any error
set -e

# Function to display usage
usage() {
    echo "Usage: $0 {start|stop|status}"
    echo "  start       Start the resinkit API service"
    echo "  stop        Stop the resinkit API service"
    echo "  status      Check status of resinkit API service"
    echo ""
    echo "Environment variables:"
    echo "  RESINKIT_API_GITHUB_TOKEN  If set, install from local repository instead of PyPI"
    echo "  RESINKIT_API_DEBUG_PORT    If set, run in debug mode, usually 5678"
    exit 1
}


export RESINKIT_API_SERVICE_PORT="${RESINKIT_API_SERVICE_PORT:-8602}"
export RESINKIT_API_LOG_FILE="${RESINKIT_API_LOG_FILE:-/dev/null}"
export RESINKIT_API_PATH="${RESINKIT_API_PATH:-/opt/resinkit/api}"

UV_BIN="/home/resinkit/.local/bin/uv"
if [ ! -f "$UV_BIN" ]; then
    echo "[RESINKIT] UV not installed"
    exit 1
fi

# Function to install dependencies
install_dependencies() {
    echo "[RESINKIT] Installing dependencies..."
    # Check if pyproject.toml exists in the resinkit-api folder
    if [[ -f "$RESINKIT_API_PATH/pyproject.toml" ]]; then
        echo "[RESINKIT] Installing from local repository (pyproject.toml found)..."
        $UV_BIN --directory "$RESINKIT_API_PATH" sync
    else
        echo "[RESINKIT] Installing from PyPI (pyproject.toml not found)..."
        $UV_BIN --directory "$RESINKIT_API_PATH" venv --python 3.12 "$RESINKIT_API_PATH/.venv"
        $UV_BIN --directory "$RESINKIT_API_PATH" pip install uvicorn resinkit-api-python -U
    fi

    # install debugpy if debug port is set
    if [[ -n "$RESINKIT_API_DEBUG_PORT" ]]; then
        echo "[RESINKIT] Debug port is set: $RESINKIT_API_DEBUG_PORT, installing debugpy..."
        $UV_BIN --directory "$RESINKIT_API_PATH" pip install debugpy
    fi
}

run_alembic_migrations() {
    echo "[RESINKIT] Running alembic migrations..."
    $UV_BIN --directory "$RESINKIT_API_PATH" run alembic -c "$RESINKIT_API_PATH/resinkit_api/db/alembic.ini" upgrade head
}

# Function to start the service
start_service() {
    set -x
    # Check if service is already running
    if pgrep -f "uvicorn resinkit_api.main:app" >/dev/null; then
        echo "[RESINKIT] Resinkit API service is already running"
        return 0
    fi

    cd "$RESINKIT_API_PATH"

    install_dependencies

    run_alembic_migrations

    # Start the service
    echo "[RESINKIT] Starting resinkit_api service..."

    if [[ "$RESINKIT_API_LOG_FILE" != "/dev/null" ]]; then
        mkdir -p "$(dirname "$RESINKIT_API_LOG_FILE")"
        touch "$RESINKIT_API_LOG_FILE"
    fi

    # if debug port is set, run uvicorn with debugpy, otherwise run uvicorn directly
    if [[ -n "$RESINKIT_API_DEBUG_PORT" ]]; then
        nohup "$RESINKIT_API_PATH/.venv/bin/python3" "-m" "debugpy" "--listen" "0.0.0.0:$RESINKIT_API_DEBUG_PORT" "-m" "uvicorn" "resinkit_api.main:app" "--host" "0.0.0.0" "--port" "$RESINKIT_API_SERVICE_PORT" >"$RESINKIT_API_LOG_FILE" 2>&1 &
    else
        nohup "$RESINKIT_API_PATH/.venv/bin/python3" "$RESINKIT_API_PATH/.venv/bin/uvicorn" resinkit_api.main:app --host 0.0.0.0 --port "$RESINKIT_API_SERVICE_PORT" >"$RESINKIT_API_LOG_FILE" 2>&1 &
    fi

    # Get the PID and save it
    local pid=$!
    echo "[RESINKIT] Resinkit API service started with PID: $pid"
    echo "[RESINKIT] Logs are being written to: $RESINKIT_API_LOG_FILE"
    set +x
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

# Function to check status of resinkit API service
status_service() {
    echo "[RESINKIT] Checking resinkit API service status..."
    
    # Check if resinkit API is running
    local pids=$(pgrep -f "uvicorn resinkit_api.main:app" || true)
    
    if [[ -n "$pids" ]]; then
        echo "[RESINKIT] ✅ Resinkit API service is running"
        echo "[RESINKIT]   API PIDs: $pids"
        echo "[RESINKIT]   Service port: $RESINKIT_API_SERVICE_PORT"
        echo "[RESINKIT]   Log file: $RESINKIT_API_LOG_FILE"
        
        # Test API accessibility
        if curl -s --connect-timeout 5 http://localhost:$RESINKIT_API_SERVICE_PORT/health >/dev/null 2>&1; then
            echo "[RESINKIT] ✅ Resinkit API accessible at http://localhost:$RESINKIT_API_SERVICE_PORT"
        elif curl -s --connect-timeout 5 http://localhost:$RESINKIT_API_SERVICE_PORT >/dev/null 2>&1; then
            echo "[RESINKIT] ✅ Resinkit API accessible at http://localhost:$RESINKIT_API_SERVICE_PORT"
        else
            echo "[RESINKIT] ❌ Resinkit API not accessible at http://localhost:$RESINKIT_API_SERVICE_PORT"
        fi

        if [[ "$RESINKIT_API_LOG_FILE" != "/dev/null" ]]; then
            if [[ -f "$RESINKIT_API_LOG_FILE" ]]; then
                echo "[RESINKIT] ✅ Log file exists: $RESINKIT_API_LOG_FILE"
                local log_size=$(du -h "$RESINKIT_API_LOG_FILE" | cut -f1)
                echo "[RESINKIT]   Log file size: $log_size"
            else
                echo "[RESINKIT] ❌ Log file missing: $RESINKIT_API_LOG_FILE"
            fi
        fi
    else
        echo "[RESINKIT] ❌ Resinkit API service is not running"
    fi
    
    # Check UV binary
    if [[ -f "$UV_BIN" ]]; then
        echo "[RESINKIT] ✅ UV binary found: $UV_BIN"
    else
        echo "[RESINKIT] ❌ UV binary missing: $UV_BIN"
    fi
    
    # Check API path
    if [[ -d "$RESINKIT_API_PATH" ]]; then
        echo "[RESINKIT] ✅ API path exists: $RESINKIT_API_PATH"
    else
        echo "[RESINKIT] ❌ API path missing: $RESINKIT_API_PATH"
    fi
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
