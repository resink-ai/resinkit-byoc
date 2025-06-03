#!/bin/bash
# shellcheck disable=SC1091,SC2046

set -eo pipefail

# --- Start of logging setup ---
# Get current date in YYYY-MM-DD format
CURRENT_DATE=$(date +%F)
LOG_FILE="/var/log/setup_${CURRENT_DATE}.log"
mkdir -p $(dirname "$LOG_FILE")
exec > >(tee -a "$LOG_FILE")
exec 2>&1
# --- End of logging setup ---

# Find the root directory
if git rev-parse --show-toplevel >/dev/null 2>&1; then
    ROOT_DIR=$(git rev-parse --show-toplevel)
else
    ROOT_DIR="/root/resinkit-byoc"
fi
export ROOT_DIR

# Get the directory where the script is located
SCRIPT_DIR=$ROOT_DIR/resources

# Source the modular components

source "${SCRIPT_DIR}/setup_vars.sh"
source "${SCRIPT_DIR}/setup_common.sh"
source "${SCRIPT_DIR}/setup_debian.sh"
source "${SCRIPT_DIR}/setup_debian_additional.sh"

# Initialize variables
setup_vars

# Function to show usage
show_usage() {
    set +x
    echo "[RESINKIT] Usage: $0 <command> [arguments]"
    echo "[RESINKIT] Available commands:"
    echo "[RESINKIT]   debian_install_common_packages   - Install common packages"
    echo "[RESINKIT]   debian_install_java              - Install Java"
    echo "[RESINKIT]   debian_install_flink             - Install Flink"
    echo "[RESINKIT]   debian_install_kafka             - Install Kafka"
    echo "[RESINKIT]   debian_install_flink_jars        - Install Flink jars"
    echo "[RESINKIT]   debian_install_resinkit          - Install resinkit"
    echo "[RESINKIT]   debian_install_nginx             - Install nginx"
    echo "[RESINKIT]   debian_install_gosu              - Install gosu"
    echo "[RESINKIT]   debian_install_all               - Install all"
    echo "[RESINKIT]   debian_install_admin_tools       - Install admin tools"
    echo "[RESINKIT]   help                             - Show usage"
}

# Main argument parsing
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

# Get the command (first argument)
cmd=$1
shift # Remove the first argument, leaving any remaining args

if [ "$1" = "-f" ]; then
    echo "[RESINKIT] Running tail -f, foreground mode"
    export RUNNING_TAIL_F=true
else
    echo "[RESINKIT] Not running tail -f, background mode"
    export RUNNING_TAIL_F=false
fi

# Parse command and execute corresponding function
echo "================================================"
echo "Running command: $cmd"
echo "================================================"
case $cmd in
"debian_install_common_packages")
    debian_install_common_packages
    ;;
"debian_install_java")
    debian_install_java
    ;;
"debian_install_flink")
    debian_install_flink
    ;;
"debian_install_gosu")
    debian_install_gosu
    ;;
"debian_install_kafka")
    debian_install_kafka
    ;;
"debian_install_flink_jars")
    debian_install_flink_jars
    ;;
"debian_install_resinkit")
    debian_install_resinkit
    ;;
"debian_install_nginx")
    debian_install_nginx
    ;;
"debian_install_admin_tools")
    debian_install_admin_tools
    ;;
"debian_install_mariadb")
    debian_install_mariadb
    ;;
"debian_install_minio")
    debian_install_minio
    ;;
"debian_install_all")
    debian_install_all
    ;;
"debian_install_additional")
    debian_install_mariadb
    debian_install_minio
    ;;
"run_entrypoint")
    run_entrypoint
    ;;
"run_curl_test")
    run_curl_test
    ;;
"run_tail_f")
    tail -f /dev/null
    ;;
"help" | "-h" | "--help")
    show_usage
    ;;
*)
    echo "[RESINKIT] Error: Unknown command '$cmd'"
    show_usage
    exit 1
    ;;
esac
