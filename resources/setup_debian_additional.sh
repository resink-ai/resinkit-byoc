#!/bin/bash
# shellcheck disable=SC1091,SC2086

# Debian-specific installation functions for ResInKit

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

# Source the common functions and variables
source "$ROOT_DIR/resources/setup_vars.sh"
source "$ROOT_DIR/resources/setup_common.sh"

function debian_install_mariadb() {
    # Check if MariaDB is already installed
    if [ -d "/var/lib/mysql" ] && [ -f "/opt/setup/.mariadb_installed" ]; then
        echo "[RESINKIT] MariaDB already installed, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing MariaDB server..."

    # Set debconf selections to avoid interactive prompts
    export DEBIAN_FRONTEND=noninteractive

    # Install MariaDB server and client
    apt-get update
    apt-get install -y mariadb-server mariadb-client

    # Start MariaDB service - check for available service management tools
    if command -v systemctl >/dev/null 2>&1; then
        echo "[RESINKIT] Using systemctl to manage MariaDB service..."
        systemctl start mariadb
        systemctl enable mariadb
    elif command -v service >/dev/null 2>&1; then
        echo "[RESINKIT] Using service command to manage MariaDB service..."
        service mariadb start
        # Enable service for startup (try different methods)
        if command -v update-rc.d >/dev/null 2>&1; then
            update-rc.d mariadb enable
        elif command -v chkconfig >/dev/null 2>&1; then
            chkconfig mariadb on
        else
            echo "[RESINKIT] Warning: Could not enable MariaDB service for startup"
        fi
    else
        echo "[RESINKIT] Error: Neither systemctl nor service command available for managing MariaDB service"
        return 1
    fi

    # Wait for MariaDB to be ready
    echo "[RESINKIT] Waiting for MariaDB to start..."
    sleep 5

    # Configure MariaDB with binlog enabled
    echo "[RESINKIT] Configuring MariaDB with binary logging..."

    # Create custom MariaDB configuration for binlog
    cat >/etc/mysql/mariadb.conf.d/60-resinkit.cnf <<EOF
[mysqld]
# Binary logging configuration
log-bin=mysql-bin
server-id=1
binlog-format=ROW
expire-logs-days=7
max-binlog-size=100M

# Other useful settings
bind-address=0.0.0.0
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci

# Performance settings
innodb_buffer_pool_size=256M
innodb_log_file_size=64M
innodb_flush_log_at_trx_commit=1
sync_binlog=1
EOF

    # Restart MariaDB to apply configuration
    if command -v systemctl >/dev/null 2>&1; then
        echo "[RESINKIT] Restarting MariaDB using systemctl..."
        systemctl restart mariadb
    elif command -v service >/dev/null 2>&1; then
        echo "[RESINKIT] Restarting MariaDB using service command..."
        service mariadb restart
    else
        echo "[RESINKIT] Error: Neither systemctl nor service command available for restarting MariaDB"
        return 1
    fi

    # Wait for MariaDB to restart
    echo "[RESINKIT] Waiting for MariaDB to restart with new configuration..."
    sleep 5

    # Set root password if MYSQL_ROOT_PASSWORD is provided
    if [ -n "$MYSQL_ROOT_PASSWORD" ]; then
        echo "[RESINKIT] Setting MariaDB root password..."

        # Use mysql to set the root password
        mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '$MYSQL_ROOT_PASSWORD';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF

        echo "[RESINKIT] MariaDB root password has been set"

        # Create .my.cnf for root user to avoid password prompts
        cat >/root/.my.cnf <<EOF
[client]
user=root
password=$MYSQL_ROOT_PASSWORD
EOF
        chmod 600 /root/.my.cnf

        # Create /etc/mysql/debian.cnf for Debian maintenance scripts
        cat >/etc/mysql/debian.cnf <<EOF
[client]
host     = localhost
user     = root
password = $MYSQL_ROOT_PASSWORD
[mysql_upgrade]
host     = localhost
user     = root
password = $MYSQL_ROOT_PASSWORD
EOF
        chmod 600 /etc/mysql/debian.cnf

    else
        echo "[RESINKIT] Warning: MYSQL_ROOT_PASSWORD not set, MariaDB root password not configured"
        echo "[RESINKIT] You may want to run mysql_secure_installation manually"
    fi

    # Verify MariaDB installation and binlog status
    echo "[RESINKIT] Verifying MariaDB installation..."
    if mysql -u root -e "SHOW VARIABLES LIKE 'log_bin';" | grep -q "ON"; then
        echo "[RESINKIT] ✅ MariaDB binary logging is enabled"
    else
        echo "[RESINKIT] ❌ MariaDB binary logging is not enabled"
        return 1
    fi

    # Show MariaDB status
    if command -v systemctl >/dev/null 2>&1; then
        systemctl status mariadb --no-pager
    elif command -v service >/dev/null 2>&1; then
        service mariadb status
    else
        echo "[RESINKIT] Warning: Cannot check MariaDB status - neither systemctl nor service command available"
    fi

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.mariadb_installed

    echo "[RESINKIT] ✅ MariaDB installation completed successfully"
}

function debian_install_minio() {
    # Check if Minio is already installed
    if [ -d "/opt/minio" ] && [ -f "/opt/setup/.minio_installed" ]; then
        echo "[RESINKIT] Minio already installed, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing MinIO server..."

    # Set default MinIO configuration
    export MINIO_ROOT_USER=${MINIO_ROOT_USER:-admin}
    export MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD:-cnk8_}
    export MINIO_DATA_DIR=${MINIO_DATA_DIR:-/opt/minio/data}
    export MINIO_CONFIG_DIR=${MINIO_CONFIG_DIR:-/opt/minio/config}
    export MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT:-9001}
    export MINIO_API_PORT=${MINIO_API_PORT:-9000}

    # Create MinIO user
    echo "[RESINKIT] Creating MinIO user..."
    if ! id -u minio >/dev/null 2>&1; then
        useradd --system --no-create-home --shell /bin/false minio
        echo "[RESINKIT] MinIO user created"
    else
        echo "[RESINKIT] MinIO user already exists"
    fi

    # Create MinIO directories
    echo "[RESINKIT] Creating MinIO directories..."
    mkdir -p /opt/minio/bin
    mkdir -p "$MINIO_DATA_DIR"
    mkdir -p "$MINIO_CONFIG_DIR"
    mkdir -p /var/log/minio

    # Download MinIO binary if not already installed
    if [ ! -f "/opt/minio/bin/minio" ]; then
        ARCH=$(dpkg --print-architecture)
        MINIO_BINARY_URL="https://dl.min.io/server/minio/release/linux-${ARCH}/minio"
        echo "[RESINKIT] Downloading MinIO binary from $MINIO_BINARY_URL..."
        # Download with retry logic
        for attempt in 1 2 3; do
            if wget -q --show-progress "$MINIO_BINARY_URL" -O /opt/minio/bin/minio; then
                echo "[RESINKIT] MinIO binary downloaded successfully"
                break
            else
                echo "[RESINKIT] Attempt $attempt failed, retrying..."
                sleep 5
            fi
            if [ $attempt -eq 3 ]; then
                echo "[RESINKIT] Error: Failed to download MinIO binary after 3 attempts"
                return 1
            fi
        done

        # Make binary executable
        chmod +x /opt/minio/bin/minio

        # Verify binary
        if ! /opt/minio/bin/minio --version >/dev/null 2>&1; then
            echo "[RESINKIT] Error: MinIO binary verification failed"
            return 1
        fi

        echo "[RESINKIT] MinIO binary installed and verified"
    fi

    # Download MinIO Client (mc) for administration if not already installed
    if [ ! -f "/opt/minio/bin/mc" ]; then
        echo "[RESINKIT] Downloading MinIO Client (mc)..."
        MC_BINARY_URL="https://dl.min.io/client/mc/release/linux-${ARCH}/mc"

        for attempt in 1 2 3; do
            if wget -q --show-progress "$MC_BINARY_URL" -O /opt/minio/bin/mc; then
                echo "[RESINKIT] MinIO Client downloaded successfully"
                break
            else
                echo "[RESINKIT] Attempt $attempt failed, retrying..."
                sleep 5
            fi
            if [ $attempt -eq 3 ]; then
                echo "[RESINKIT] Warning: Failed to download MinIO Client after 3 attempts"
                # Continue without mc as it's not critical
                break
            fi
        done

        if [ -f /opt/minio/bin/mc ]; then
            chmod +x /opt/minio/bin/mc
            echo "[RESINKIT] MinIO Client installed"
        fi
    fi

    # Set ownership
    chown -R minio:minio /opt/minio
    chown -R minio:minio /var/log/minio

    # Create MinIO environment file
    echo "[RESINKIT] Creating MinIO environment configuration..."
    cat >/etc/default/minio <<EOF
# MinIO configuration
MINIO_ROOT_USER=$MINIO_ROOT_USER
MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD
MINIO_VOLUMES=$MINIO_DATA_DIR
MINIO_OPTS="--console-address :$MINIO_CONSOLE_PORT --address :$MINIO_API_PORT"
EOF

    # Create systemd service file
    if command -v systemctl >/dev/null 2>&1; then
        echo "[RESINKIT] Creating MinIO systemd service..."
        cat >/etc/systemd/system/minio.service <<EOF
[Unit]
Description=MinIO
Documentation=https://min.io/docs/minio/linux/index.html
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/opt/minio/bin/minio

[Service]
WorkingDirectory=/opt/minio
User=minio
Group=minio
EnvironmentFile=-/etc/default/minio
ExecStartPre=/bin/bash -c 'if [ -z "\${MINIO_VOLUMES}" ]; then echo "Variable MINIO_VOLUMES not set in /etc/default/minio"; exit 1; fi'
ExecStart=/opt/minio/bin/minio server \$MINIO_OPTS \$MINIO_VOLUMES
StandardOutput=journal
StandardError=inherit
SyslogIdentifier=minio
KillSignal=SIGTERM
SendSIGKILL=no
SuccessExitStatus=0
LimitNOFILE=1048576
LimitNPROC=1048576
LimitCORE=infinity
TimeoutStopSec=infinity

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd and start MinIO
        systemctl daemon-reload
        systemctl enable minio
        systemctl start minio

        # Wait for MinIO to start
        echo "[RESINKIT] Waiting for MinIO to start..."
        sleep 10

        # Check MinIO status
        if systemctl is-active --quiet minio; then
            echo "[RESINKIT] ✅ MinIO service is running"
            systemctl status minio --no-pager
        else
            echo "[RESINKIT] ❌ MinIO service failed to start"
            systemctl status minio --no-pager
            return 1
        fi

    elif command -v service >/dev/null 2>&1; then
        echo "[RESINKIT] Creating MinIO init script..."
        cat >/etc/init.d/minio <<'EOF'
#!/bin/bash
### BEGIN INIT INFO
# Provides:          minio
# Required-Start:    $remote_fs $syslog
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: MinIO object storage server
# Description:       MinIO is a High Performance Object Storage
### END INIT INFO

. /lib/lsb/init-functions

USER="minio"
DAEMON="minio"
ROOT_DIR="/opt/minio"
DAEMON_FILE="$ROOT_DIR/bin/$DAEMON"
LOCK_FILE="/var/lock/subsys/minio"

start() {
    if [ -f $LOCK_FILE ] ; then
        echo "$DAEMON is locked."
        return 1
    fi

    # Source environment
    [ -r /etc/default/minio ] && . /etc/default/minio

    echo -n $"Starting $DAEMON: "
    daemon --user "$USER" --pidfile="$LOCK_FILE" \
        $DAEMON_FILE server $MINIO_OPTS $MINIO_VOLUMES
    RETVAL=$?
    echo
    [ $RETVAL -eq 0 ] && touch $LOCK_FILE
    return $RETVAL
}

stop() {
    echo -n $"Shutting down $DAEMON: "
    pid=`ps -aefw | grep "$DAEMON" | grep -v " grep " | awk '{print $2}'`
    kill -9 $pid > /dev/null 2>&1
    [ $? -eq 0 ] && echo "OK" || echo "Failed"
    rm -f $LOCK_FILE
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    status)
        if [ -f $LOCK_FILE ]; then
            echo "$DAEMON is running."
        else
            echo "$DAEMON is stopped."
        fi
        ;;
    restart)
        stop
        start
        ;;
    *)
        echo "Usage: {start|stop|status|restart}"
        exit 1
        ;;
esac

exit $?
EOF

        chmod +x /etc/init.d/minio

        # Enable and start service
        if command -v update-rc.d >/dev/null 2>&1; then
            update-rc.d minio defaults
        elif command -v chkconfig >/dev/null 2>&1; then
            chkconfig --add minio
            chkconfig minio on
        fi

        service minio start
        echo "[RESINKIT] MinIO service started"

    else
        echo "[RESINKIT] Warning: Neither systemctl nor service command available"
        echo "[RESINKIT] MinIO installed but service not configured"
        echo "[RESINKIT] You can start MinIO manually with: sudo -u minio /opt/minio/bin/minio server $MINIO_DATA_DIR"
    fi

    # Configure MinIO client if available
    if [ -f /opt/minio/bin/mc ]; then
        echo "[RESINKIT] Configuring MinIO client..."
        # Wait a bit more for MinIO to be fully ready
        sleep 5

        # Configure mc as minio user
        sudo -u minio /opt/minio/bin/mc alias set local http://localhost:$MINIO_API_PORT $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD 2>/dev/null || true
        echo "[RESINKIT] MinIO client configured"
    fi

    # Add MinIO binaries to PATH
    if ! grep -q "/opt/minio/bin" /etc/environment; then
        echo 'PATH="/opt/minio/bin:$PATH"' >>/etc/environment
        echo "[RESINKIT] MinIO binaries added to PATH"
    fi

    # Display connection information
    echo "[RESINKIT] ✅ MinIO installation completed successfully"
    echo "[RESINKIT] MinIO API: http://localhost:$MINIO_API_PORT"
    echo "[RESINKIT] MinIO Console: http://localhost:$MINIO_CONSOLE_PORT"
    echo "[RESINKIT] Root User: $MINIO_ROOT_USER"
    echo "[RESINKIT] Root Password: $MINIO_ROOT_PASSWORD"
    echo "[RESINKIT] Data Directory: $MINIO_DATA_DIR"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.minio_installed
}
