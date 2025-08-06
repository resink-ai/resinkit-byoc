#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046

: "${ROOT_DIR:?}"

function install_mariadb() {
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
    if ls -la /run/systemd/system/ >/dev/null 2>&1; then
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
default-time-zone = '+00:00'

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
    if ls -la /run/systemd/system/ >/dev/null 2>&1; then
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

    # Execute create_tables.sql if MYSQL_RESINKIT_PASSWORD is provided
    if [ -n "$MYSQL_RESINKIT_PASSWORD" ]; then
        echo "[RESINKIT] Executing create_tables.sql with root privileges..."
        if [ -f "$ROOT_DIR/resources/test-mysql/create_tables.sql" ]; then
            # Replace the password placeholder in the SQL file and execute
            sed "s/resinkit_mysql_password/$MYSQL_RESINKIT_PASSWORD/g" "$ROOT_DIR/resources/test-mysql/create_tables.sql" | mysql -u root
            echo "[RESINKIT] ✅ Database setup completed using create_tables.sql"
        else
            echo "[RESINKIT] Error: create_tables.sql not found at $ROOT_DIR/resources/test-mysql/create_tables.sql"
            return 1
        fi
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
    if ls -la /run/systemd/system/ >/dev/null 2>&1; then
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

install_mariadb
