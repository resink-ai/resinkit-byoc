#!/bin/bash
# Setup and run the service in EC2 or a container
set -eo pipefail

# Configuration variables
RESINKIT_API_VENV_DIR="${RESINKIT_API_VENV_DIR:-/opt/resinkit/api/.venv}"
RESINKIT_API_PATH="${RESINKIT_API_PATH:-/opt/resinkit/api}"
RESINKIT_API_LOG_FILE="${RESINKIT_API_LOG_FILE:-/opt/resinkit/logs/resinkit_api.log}"
RESINKIT_API_SERVICE_PORT="${RESINKIT_API_SERVICE_PORT:-8602}"

# exist if APP_DIR does not exist
if [[ ! -d "$RESINKIT_API_PATH" ]]; then
    echo "[QQQ] App directory does not exist"
    exit 1
fi

install_python_uv() {
    # Step 0: skip if python3.12 and uv are already installed
    if command -v python3.12 &>/dev/null && command -v uv &>/dev/null; then
        echo "[QQQ] Python 3.12 and uv already installed"
        return 0
    fi

    # Step 1: install pyenv
    curl https://pyenv.run | bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv virtualenv-init -)"

    # Step 2: install python 3.12
    pyenv install 3.12

    # Step 3: install uv
    uv venv --python 3.12 "$RESINKIT_API_VENV_DIR"

    # Step 4: create virtual environment at $RESINKIT_API_VENV_DIR
}

# Create a Python 3.11 virtual environment if it doesn't exist
if [[ ! -f "$RESINKIT_API_VENV_DIR/bin/activate" ]]; then
    echo "[QQQ] Creating Python virtual environment..."
    rm -rf "$RESINKIT_API_VENV_DIR"
    python3 -m venv "$RESINKIT_API_VENV_DIR"
fi

# Activate virtual environment
# shellcheck source=/dev/null
source "$RESINKIT_API_VENV_DIR/bin/activate"

# Upgrade pip in the virtual environment
echo "[QQQ] Upgrading pip..."
pip install --upgrade pip

# Install Poetry and uvicorn if not already installed
if ! command -v poetry &>/dev/null; then
    echo "[QQQ] Installing Poetry..."
    pip install poetry
fi

pip install uvicorn

# Verify Poetry installation
poetry --version

# Navigate to the application directory
cd "$RESINKIT_API_PATH"

# Configure Poetry to use the existing virtual environment
poetry config virtualenvs.create false

# Install dependencies using Poetry
echo "[QQQ] Installing resinkit_api dependencies..."
poetry install

# Create log directory if it doesn't exist
RESINKIT_API_LOG_DIR=$(dirname "$RESINKIT_API_LOG_FILE")
if [[ ! -d "$RESINKIT_API_LOG_DIR" ]]; then
    echo "[QQQ] Creating log directory..."
    mkdir -p "$RESINKIT_API_LOG_DIR"
fi

# Check if service is already running
if pgrep -f "uvicorn resinkit_api.main:app" >/dev/null; then
    echo "[QQQ] Resinkit_api service already running"
    # Optionally restart the service
    echo "[QQQ] Restarting service..."
    pkill -f "uvicorn resinkit_api.main:app"
    sleep 2
fi

# Run the FastAPI service using the virtual environment
echo "[QQQ] Starting resinkit_api service..."
ENV=production nohup "$RESINKIT_API_VENV_DIR/bin/uvicorn" resinkit_api.main:app --host 0.0.0.0 --port "$RESINKIT_API_SERVICE_PORT" >"$RESINKIT_API_LOG_FILE" 2>&1 &

# Wait a moment and check if the service started successfully
sleep 3
if pgrep -f "uvicorn resinkit_api.main:app" >/dev/null; then
    echo "[QQQ] Resinkit_api service started successfully"
    echo "[QQQ] Service is running at http://localhost:$RESINKIT_API_SERVICE_PORT"
    echo "[QQQ] Logs are available at $RESINKIT_API_LOG_FILE"
else
    echo "[QQQ] Failed to start resinkit_api service. Check logs at $RESINKIT_API_LOG_FILE"
    exit 1
fi

echo "[QQQ] Resinkit_api service setup complete"
