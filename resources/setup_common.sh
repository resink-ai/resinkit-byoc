#!/bin/bash
# shellcheck disable=SC1091

# Common utility functions for ResInKit setup

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

# Source the variables (assume variables are set)
source "$ROOT_DIR/resources/setup_vars.sh"

# Function to determine the command to drop privileges
drop_privs_cmd() {
    if [ "$(id -u)" != 0 ]; then
        # Don't need to drop privs if EUID != 0
        return
    elif [ -x /sbin/su-exec ]; then
        # Alpine
        echo su-exec "$RESINKIT_ROLE"
    else
        # Others
        echo gosu "$RESINKIT_ROLE"
    fi
}

# Function to verify GPG signatures
# Usage: verify_gpg_signature <file> <signature_file> <gpg_key> [retries]
verify_gpg_signature() {
    local file="$1"         # Original file to verify
    local sig_file="$2"     # Path to the signature file
    local gpg_key="$3"      # GPG key to verify against
    local retries="${4:-3}" # Number of retries, default 3

    # Validate required parameters
    if [[ -z "$file" || -z "$sig_file" || -z "$gpg_key" ]]; then
        echo "[RESINKIT] Usage: verify_gpg_signature <file> <signature_file> <gpg_key> [retries]"
        return 1
    fi

    # Check if original file exists
    if [[ ! -f "$file" ]]; then
        echo "[RESINKIT] Error: File '$file' not found"
        return 1
    fi

    # Check if signature file exists
    if [[ ! -f "$sig_file" ]]; then
        echo "[RESINKIT] Error: Signature file '$sig_file' not found"
        return 1
    fi

    # Create temporary GPG home directory
    GNUPGHOME="$(mktemp -d)"

    # Define reliable keyservers
    local key_servers=(
        "keyserver.ubuntu.com"
        "hkp://keyserver.ubuntu.com:80"
        "keys.openpgp.org"
        "hkps://keys.openpgp.org"
        "pgp.mit.edu"
        "hkp://pgp.mit.edu:80"
        "keyring.debian.org"
        "hkp://keyring.debian.org:80"
    )

    # Try to import the GPG key
    local key_imported=0
    local attempt=1
    while [[ $attempt -le $retries && $key_imported -eq 0 ]]; do
        echo "[RESINKIT] Attempt $attempt of $retries to import GPG key..."
        for server in "${key_servers[@]}"; do
            echo "[RESINKIT] Trying keyserver: $server"
            if gpg --batch --keyserver "$server" --recv-keys "$gpg_key" 2>/dev/null; then
                key_imported=1
                break
            fi
            sleep 1
        done

        ((attempt++))
    done

    # Check if key import was successful
    if [[ $key_imported -eq 0 ]]; then
        echo "[RESINKIT] Error: Failed to import GPG key after $retries attempts"
        rm -rf "$GNUPGHOME"
        return 1
    fi

    # Verify the signature
    local verify_result=0
    if ! gpg --batch --verify "$sig_file" "$file" 2>/dev/null; then
        echo "[RESINKIT] Error: GPG verification failed for $file"
        verify_result=1
    else
        echo "[RESINKIT] GPG verification successful for $file"
    fi

    # Cleanup
    gpgconf --kill all
    rm -rf "$GNUPGHOME"

    return $verify_result
}

run_jupyter() {
    # start jupyterlab using the jupyter user's entrypoint script
    echo "[RESINKIT] Starting Jupyter service..."

    # Check if jupyter user exists
    if ! id "jupyter" &>/dev/null; then
        echo "[RESINKIT] Error: User 'jupyter' does not exist. Run setup_jupyter first."
        return 1
    fi

    # Check if entrypoint script exists
    if [ ! -f "/home/jupyter/bin/jupyter_entrypoint.sh" ]; then
        echo "[RESINKIT] Error: Jupyter entrypoint script not found. Run setup_jupyter first."
        return 1
    fi

    chown -R jupyter:jupyter /home/jupyter

    # Start jupyter as the jupyter user
    if [ "$(id -u)" = 0 ]; then
        # Running as root, switch to jupyter user
        gosu jupyter /home/jupyter/bin/jupyter_entrypoint.sh start
    else
        # Not running as root, check if we're the jupyter user
        if [ "$(whoami)" = "jupyter" ]; then
            /home/jupyter/bin/jupyter_entrypoint.sh start
        else
            echo "[RESINKIT] Error: Must run as root or jupyter user"
            return 1
        fi
    fi
}

run_entrypoint() {
    # start or reload nginx with root
    if [ -f /.dockerenv ]; then
        echo "[RESINKIT] Running inside Docker"
        nginx || nginx -s reload || true
    else
        echo "[RESINKIT] Not running inside Docker"
        systemctl enable nginx || true
        systemctl start nginx || true
    fi

    # start jupyter
    run_jupyter

    # Check if entrypoint.sh already exists
    if [ ! -f "$RESINKIT_ENTRYPOINT_SH" ]; then
        mkdir -p "$(dirname "$RESINKIT_ENTRYPOINT_SH")"
        cp -v "$ROOT_DIR/resources/entrypoint.sh" "$RESINKIT_ENTRYPOINT_SH"
    else
        echo "[RESINKIT] Entrypoint script already exists at $RESINKIT_ENTRYPOINT_SH, skipping copy"
    fi

    # /opt/flink, /opt/kafka, /opt/flink-cdc, /opt/resinkit
    chown -R "$RESINKIT_ROLE":"$RESINKIT_ROLE" "$FLINK_HOME"
    chown -R "$RESINKIT_ROLE":"$RESINKIT_ROLE" "$KAFKA_HOME"
    chown -R "$RESINKIT_ROLE":"$RESINKIT_ROLE" "$FLINK_CDC_HOME"
    chown -R "$RESINKIT_ROLE":"$RESINKIT_ROLE" "$(dirname "$RESINKIT_API_PATH")"
    exec $(drop_privs_cmd) "$RESINKIT_ENTRYPOINT_SH"
}

run_curl_test() {
    echo "[RESINKIT] Testing flink & flink sql gateway"
    curl -s http://localhost:8083/info | jq .
    curl -s http://localhost:8081/config | jq .
    curl -s -H "Authorization: pat_cnk8_" http://127.0.0.1:8602/api/v1/pat/validate | jq .

    echo "[RESINKIT] Testing nginx reverse proxy"
    BASE_URL="http://localhost:8080"
    curl -s -H "Authorization: pat_cnk8_" "$BASE_URL/flink_sql_gateway/info" | jq .
    curl -s -H "Authorization: pat_cnk8_" "$BASE_URL/flink_ui/config" | jq .
}
