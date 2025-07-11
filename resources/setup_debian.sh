#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046
# Debian-specific installation functions for ResInKit

[[ -z "$ROOT_DIR" ]] && echo "[RESINKIT] Error: ROOT_DIR is not set" && exit 1

# Source the common functions and variables
source "$ROOT_DIR/resources/setup_vars.sh"
source "$ROOT_DIR/resources/setup_common.sh"

function debian_install_common_packages() {
    # Check if packages are already installed
    if [ -f "/opt/setup/.common_packages_installed" ]; then
        echo "[RESINKIT] Common packages already installed, skipping"
        return 0
    fi

    export TZ=UTC
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y --no-install-recommends \
        vim \
        wget \
        gnupg \
        nginx \
        iputils-ping \
        mariadb-client \
        telnet \
        ca-certificates \
        gnupg \
        git \
        ca-certificates \
        make \
        curl \
        zsh \
        wget
    apt-get install -y --no-install-recommends \
        build-essential \
        zlib1g-dev \
        libncurses5-dev \
        libgdbm-dev \
        libnss3-dev \
        libssl-dev \
        libreadline-dev \
        libffi-dev \
        libsqlite3-dev \
        libbz2-dev \
        pkg-config \
        liblzma-dev

    apt-get install -y python3 python3-pip python3-dev python3-venv libpcre3-dev

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.common_packages_installed
}

function debian_install_java() {
    # Check if Java is already installed
    if [ -f "/opt/setup/.java_installed" ]; then
        echo "[RESINKIT] Java already installed, skipping"
        return 0
    fi

    ARCH=$(dpkg --print-architecture)
    export ARCH
    apt-get install -y openjdk-17-jdk openjdk-17-jre
    update-alternatives --set java "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/java"
    update-alternatives --set javac "/usr/lib/jvm/java-17-openjdk-${ARCH}/bin/javac"
    export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-${ARCH}
    apt-get install -y --no-install-recommends maven
    mvn --version

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.java_installed
}

function debian_install_hadoop() {
    # Check if Hadoop is already installed
    if [ -d "$HADOOP_HOME" ] && [ -f "/opt/setup/.hadoop_installed" ]; then
        echo "[RESINKIT] Hadoop already installed, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing Hadoop $HADOOP_VERSION for Iceberg integration (following official guide)"

    # Download and extract Hadoop as per Iceberg guide
    wget ${APACHE_HADOOP_URL}/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz -O /tmp/hadoop-${HADOOP_VERSION}.tar.gz
    tar xzvf /tmp/hadoop-${HADOOP_VERSION}.tar.gz -C /opt/
    mv /opt/hadoop-${HADOOP_VERSION} $HADOOP_HOME
    rm /tmp/hadoop-${HADOOP_VERSION}.tar.gz

    # Ensure proper permissions and ownership
    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE $HADOOP_HOME 2>/dev/null || true
    chmod +x $HADOOP_HOME/bin/hadoop

    # Verify installation
    if [ -f "$HADOOP_HOME/bin/hadoop" ]; then
        echo "[RESINKIT] Hadoop installed successfully at $HADOOP_HOME"
        echo "[RESINKIT] Hadoop version: $($HADOOP_HOME/bin/hadoop version | head -1)"
    else
        echo "[RESINKIT] Error: Hadoop installation failed"
        return 1
    fi

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.hadoop_installed
}

function debian_install_flink() {
    # Check if Flink is already installed
    if [ -d "$FLINK_HOME" ] && [ -f "/opt/setup/.flink_installed" ]; then
        echo "[RESINKIT] Flink already installed, skipping"
        return 0
    fi

    apt-get -y install gpg libsnappy1v5 gettext-base libjemalloc-dev
    rm -rf /var/lib/apt/lists/*
    # skip install gosu
    echo "[RESINKIT] FLINK_VER_MINOR: $FLINK_VER_MINOR"
    FLINK_VER_MINOR=${FLINK_VER_MINOR:-1.20.1}
    echo "[RESINKIT] FLINK_VER_MINOR: $FLINK_VER_MINOR"
    # https://dlcdn.apache.org/flink/flink-1.20.1/flink-1.20.1-bin-scala_2.12.tgz
    export FLINK_TGZ_URL=https://dlcdn.apache.org/flink/flink-${FLINK_VER_MINOR}/flink-${FLINK_VER_MINOR}-bin-scala_2.12.tgz
    export RESINKIT_ROLE=${RESINKIT_ROLE:-resinkit}
    export RESINKIT_ROLE_HOME=${RESINKIT_ROLE_HOME:-/home/resinkit}
    export FLINK_HOME=${FLINK_HOME:-/opt/flink}
    export PATH=$FLINK_HOME/bin:$PATH
    mkdir -p $FLINK_HOME

    if ! getent group "$RESINKIT_ROLE" >/dev/null; then
        groupadd --system --gid=9999 "$RESINKIT_ROLE"
    fi

    echo "[RESINKIT] Creating user $RESINKIT_ROLE with home directory $RESINKIT_ROLE_HOME"
    if ! getent passwd $RESINKIT_ROLE >/dev/null; then
        if [ ! -d "$RESINKIT_ROLE_HOME" ]; then
            mkdir -p "$RESINKIT_ROLE_HOME"
        fi
        useradd --create-home --home-dir "$RESINKIT_ROLE_HOME" --gid="$RESINKIT_ROLE" "$RESINKIT_ROLE"
        # Ensure proper ownership and permissions after user creation
        chown -R $RESINKIT_ROLE:$RESINKIT_ROLE "$RESINKIT_ROLE_HOME"
        chmod 755 "$RESINKIT_ROLE_HOME"
    else
        # User exists, but ensure home directory has proper permissions
        if [ -d "$RESINKIT_ROLE_HOME" ]; then
            chown -R $RESINKIT_ROLE:$RESINKIT_ROLE "$RESINKIT_ROLE_HOME"
            chmod 755 "$RESINKIT_ROLE_HOME"
        fi
    fi
    cd "$FLINK_HOME" || exit 1

    wget -nv -O flink.tgz "$FLINK_TGZ_URL"

    tar -xf flink.tgz --strip-components=1
    rm flink.tgz

    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE $FLINK_HOME

    # Copy rs_flink.sh to FLINK_HOME/bin/rs_flink.sh
    cp -v "$ROOT_DIR/resources/flink/bin/rs_flink.sh" "$FLINK_HOME/bin/rs_flink.sh"
    chmod +x "$FLINK_HOME/bin/rs_flink.sh"

    # Replace default REST/RPC endpoint bind address to use the container's network interface
    CONF_FILE="$FLINK_HOME/conf/flink-conf.yaml"
    if [ ! -e "$FLINK_HOME/conf/flink-conf.yaml" ]; then
        CONF_FILE="${FLINK_HOME}/conf/config.yaml"
        /bin/bash "$FLINK_HOME/bin/config-parser-utils.sh" "${FLINK_HOME}/conf" "${FLINK_HOME}/bin" "${FLINK_HOME}/lib" \
            "-repKV" "rest.address,localhost,0.0.0.0" \
            "-repKV" "rest.bind-address,localhost,0.0.0.0" \
            "-repKV" "jobmanager.bind-host,localhost,0.0.0.0" \
            "-repKV" "taskmanager.bind-host,localhost,0.0.0.0" \
            "-rmKV" "taskmanager.host=localhost"
    else
        sed -i 's/rest.address: localhost/rest.address: 0.0.0.0/g' "$CONF_FILE"
        sed -i 's/rest.bind-address: localhost/rest.bind-address: 0.0.0.0/g' "$CONF_FILE"
        sed -i 's/jobmanager.bind-host: localhost/jobmanager.bind-host: 0.0.0.0/g' "$CONF_FILE"
        sed -i 's/taskmanager.bind-host: localhost/taskmanager.bind-host: 0.0.0.0/g' "$CONF_FILE"
        sed -i '/taskmanager.host: localhost/d' "$CONF_FILE"
    fi

    # Add S3 configuration if AWS credentials are present
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        echo "[RESINKIT] Adding S3 credentials to Flink configuration"
        echo "" >>"$CONF_FILE"
        echo "s3.access-key: $AWS_ACCESS_KEY_ID" >>"$CONF_FILE"
        echo "s3.secret-key: $AWS_SECRET_ACCESS_KEY" >>"$CONF_FILE"
    fi

    # Add S3 endpoint if present and not empty
    if [ -n "$S3_ENDPOINT" ]; then
        echo "[RESINKIT] Adding S3 endpoint to Flink configuration"
        echo "" >>"$CONF_FILE"
        echo "s3.endpoint: $S3_ENDPOINT" >>"$CONF_FILE"
    fi

    # Install Hadoop and set hadoop classpath for Iceberg integration (following official Iceberg guide)
    # This ensures: export HADOOP_CLASSPATH=`$HADOOP_HOME/bin/hadoop classpath`
    debian_install_hadoop

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.flink_installed
}

function debian_install_gosu() {
    # Check if gosu is already installed
    if [ -f "/usr/local/bin/gosu" ] && [ -f "/opt/setup/.gosu_installed" ]; then
        echo "[RESINKIT] gosu already installed, skipping"
        return 0
    fi

    # Grab gosu for easy step-down from root
    export GOSU_VERSION=1.17
    rm -rf /var/lib/apt/lists/*
    dpkgArch="$(dpkg --print-architecture | awk -F- '{ print $NF }')"
    wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch"
    wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$dpkgArch.asc"
    # verify the signature
    local GOSU_GPG_KEY=B42F6819007F00F88E364FD4036A9C25BF357DD4
    verify_gpg_signature /usr/local/bin/gosu /usr/local/bin/gosu.asc $GOSU_GPG_KEY
    chmod +x /usr/local/bin/gosu
    # verify that the binary works
    gosu --version
    gosu nobody true

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.gosu_installed
}

function debian_install_kafka() {
    # Check if Kafka is already installed
    if [ -d "/opt/kafka" ] && [ -f "/opt/setup/.kafka_installed" ]; then
        echo "[RESINKIT] Kafka already installed, skipping"
        return 0
    fi

    wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz &&
        tar -xzf /tmp/kafka.tgz -C /opt &&
        mv /opt/kafka_2.12-3.4.0 /opt/kafka &&
        rm /tmp/kafka.tgz

    cp -v "$ROOT_DIR/resources/kafka/server.properties" /opt/kafka/config/server.properties

    mkdir -p /opt/kafka/logs
    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE /opt/kafka
    chmod -R 755 /opt/kafka/logs

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.kafka_installed
}

function debian_install_flink_jars() {
    # Check if Flink jars are already installed
    if [ -d "$FLINK_CDC_HOME" ] && [ -f "/opt/setup/.flink_jars_installed" ]; then
        echo "[RESINKIT] Flink jars already installed, skipping"
        return 0
    fi

    FLINK_CDC_VER=${FLINK_CDC_VER:-3.4.0}
    # Download and extract Flink CDC if not already done
    if [ ! -d "$FLINK_CDC_HOME" ]; then
        wget https://dlcdn.apache.org/flink/flink-cdc-${FLINK_CDC_VER}/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz -O /tmp/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz &&
            tar -xzf /tmp/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz -C /opt/ &&
            mv /opt/flink-cdc-${FLINK_CDC_VER} "$FLINK_CDC_HOME" &&
            rm /tmp/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz
    else
        echo "[RESINKIT] Flink CDC directory already exists, skipping extraction"
    fi

    # Download required JAR files if needed
    if [ $(find "$FLINK_HOME/lib/" -name "*.jar" | wc -l) -lt 15 ]; then
        echo "[RESINKIT] 5 or fewer jars in $FLINK_HOME/lib/, downloading"
        (
            cd "$ROOT_DIR/resources/flink/lib" || exit 1
            bash download.sh
            cp -v $ROOT_DIR/resources/flink/lib/flink/*.jar "$FLINK_HOME/lib/"
        )
    else
        echo "[RESINKIT] 15 or more jars found in $FLINK_HOME/lib/, skipping download"
    fi

    if [ $(find "$FLINK_CDC_HOME/lib/" -name "*.jar" | wc -l) -lt 15 ]; then
        echo "[RESINKIT] 5 or fewer jars in $FLINK_CDC_HOME/lib/, downloading"
        (
            cd "$ROOT_DIR/resources/flink/lib" || exit 1
            bash download.sh
            cp -v $ROOT_DIR/resources/flink/lib/cdc/*.jar "$FLINK_CDC_HOME/lib/"
        )
    else
        echo "[RESINKIT] 15 or more jars found in $FLINK_CDC_HOME/lib/, skipping download"
    fi

    # Copy plugins jars
    mkdir -p "$FLINK_HOME/plugins/"
    if [ -d "$ROOT_DIR/resources/flink/lib/plugins/" ]; then
        echo "[RESINKIT] Copying plugins jars from $ROOT_DIR/resources/flink/lib/plugins/ to $FLINK_HOME/plugins/"
        cp -rv "$ROOT_DIR/resources/flink/lib/plugins/" "$FLINK_HOME/"
    else
        echo "[RESINKIT] No plugins jars found in $ROOT_DIR/resources/flink/lib/plugins/, skipping"
    fi

    # Copy configuration files
    mkdir -p "$FLINK_HOME/conf/" "$FLINK_CDC_HOME/conf/"
    cp -v "$ROOT_DIR/resources/flink/conf/conf.yaml" "$FLINK_HOME/conf/config.yaml"
    cp -v "$ROOT_DIR/resources/flink/conf/log4j.properties" "$FLINK_HOME/conf/log4j.properties"
    cp -rv "$ROOT_DIR/resources/flink/cdc/" "$FLINK_CDC_HOME/conf/"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.flink_jars_installed
}

function debian_install_resinkit() {
    # Check if resinkit is already installed
    if [ -f "/opt/setup/.resinkit_installed" ]; then
        echo "[RESINKIT] Resinkit already installed, skipping"
        return 0
    fi

    if [ -d "$RESINKIT_API_PATH" ]; then
        echo "[RESINKIT] Resinkit API directory ($RESINKIT_API_PATH) already, first remove it"
        rm -rf "$RESINKIT_API_PATH"
    fi

    # Ensure resinkit user home directory exists and has proper permissions
    if [ ! -d "$RESINKIT_ROLE_HOME" ]; then
        echo "[RESINKIT] Creating home directory for $RESINKIT_ROLE user"
        mkdir -p "$RESINKIT_ROLE_HOME"
    fi

    # Ensure proper ownership and permissions for home directory
    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE "$RESINKIT_ROLE_HOME"
    chmod 755 "$RESINKIT_ROLE_HOME"

    # Ensure .local directory exists with proper permissions
    if [ ! -d "$RESINKIT_ROLE_HOME/.local" ]; then
        echo "[RESINKIT] Creating .local directory for $RESINKIT_ROLE user"
        mkdir -p "$RESINKIT_ROLE_HOME/.local/bin"
        chown -R $RESINKIT_ROLE:$RESINKIT_ROLE "$RESINKIT_ROLE_HOME/.local"
        chmod -R 755 "$RESINKIT_ROLE_HOME/.local"
    fi

    # Install resinkit-api
    if [ -n "$RESINKIT_API_GITHUB_TOKEN" ]; then
        echo "[RESINKIT] RESINKIT_API_GITHUB_TOKEN is set, cloning from GitHub repository"
        # Clone the repository using GitHub PAT
        git clone "https://$RESINKIT_API_GITHUB_TOKEN@github.com/resink-ai/resinkit-api-python.git" "$RESINKIT_API_PATH"
        echo "[RESINKIT] Resinkit API cloned from GitHub to $RESINKIT_API_PATH"
        # Copy entrypoint script to the API directory
        cp -v "$ROOT_DIR/resources/resinkit-api/resinkit-api-entrypoint.sh" "$RESINKIT_API_PATH/"
        echo "[RESINKIT] Entrypoint script copied to $RESINKIT_API_PATH"
    else
        echo "[RESINKIT] RESINKIT_API_GITHUB_TOKEN not set, using local resources"
        # Copy from local resources (original behavior)
        cp -rv "$ROOT_DIR/resources/resinkit-api" "$RESINKIT_API_PATH"
        echo "[RESINKIT] Resinkit API copied from resources to $RESINKIT_API_PATH"
    fi

    chown -R $RESINKIT_ROLE:$RESINKIT_ROLE "$RESINKIT_API_PATH"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.resinkit_installed
}

debian_install_jupyter() {
    # Check if jupyter is already installed
    if [ -f "/opt/setup/.jupyter_installed" ]; then
        echo "[RESINKIT] Jupyter already installed, skipping"
        return 0
    fi
    echo "[RESINKIT] Setting up Jupyter user and environment..."

    # step 1: create a user jupyter with home directory /home/jupyter
    if id "jupyter" &>/dev/null; then
        echo "[RESINKIT] User 'jupyter' already exists"
    else
        echo "[RESINKIT] Creating user 'jupyter'"
        useradd --create-home --home-dir /home/jupyter --shell /bin/bash jupyter
        echo "[RESINKIT] User 'jupyter' created with home directory /home/jupyter"
    fi

    # step 2: copy the resinkit_sample_project to /home/jupyter/workspace/resinkit_sample_project
    echo "[RESINKIT] Setting up workspace directory"
    mkdir -p /home/jupyter/workspace

    if [ -d "/home/jupyter/workspace/resinkit_sample_project" ]; then
        echo "[RESINKIT] Sample project already exists, backing up and replacing"
        rm -rf "/home/jupyter/workspace/resinkit_sample_project.bak" 2>/dev/null || true
        mv "/home/jupyter/workspace/resinkit_sample_project" "/home/jupyter/workspace/resinkit_sample_project.bak" 2>/dev/null || true
    fi

    echo "[RESINKIT] Copying resinkit_sample_project to /home/jupyter/workspace/"
    cp -r "$ROOT_DIR/resources/jupyter/resinkit_sample_project" /home/jupyter/workspace/

    # Copy the jupyter entrypoint script
    echo "[RESINKIT] Copying jupyter entrypoint script"
    mkdir -p /home/jupyter/bin
    cp "$ROOT_DIR/resources/jupyter/jupyter_entrypoint.sh" /home/jupyter/bin/
    chmod +x /home/jupyter/bin/jupyter_entrypoint.sh

    # Set up environment variables for jupyter user
    echo "[RESINKIT] Setting up environment variables"
    {
        echo "export PATH=/home/jupyter/.local/bin:\$PATH"
    } >>/home/jupyter/.bashrc

    # step 3: chown -R jupyter:jupyter /home/jupyter/
    echo "[RESINKIT] Setting ownership of /home/jupyter to jupyter:jupyter"
    chown -R jupyter:jupyter /home/jupyter/

    echo "[RESINKIT] Jupyter setup completed successfully"
    echo "[RESINKIT] To start Jupyter, run: sudo -u jupyter /home/jupyter/bin/jupyter_entrypoint.sh start"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.jupyter_installed
}

function debian_install_nginx() {
    # Check if nginx is already setup
    if [ -f "/opt/setup/.nginx_setup_completed" ]; then
        echo "[RESINKIT] Nginx already setup, skipping"
        return 0
    fi

    apt-get update && apt-get install --no-install-recommends -y nginx

    # Copy the Nginx configuration files
    # Install the main default site configuration
    cp -v "$ROOT_DIR/resources/nginx/default" /etc/nginx/sites-available/default

    # Install the reusable locations configuration
    cp -v "$ROOT_DIR/resources/nginx/resinkit_locations.conf" /etc/nginx/sites-available/resinkit_locations.conf

    # Enable the default site (create symlink if it doesn't exist)
    ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

    # Clean up old configuration files if they exist
    rm -vf /etc/nginx/sites-available/resinkit_nginx.conf || true
    rm -vf /etc/nginx/sites-enabled/resinkit_nginx.conf || true

    # Test the Nginx configuration
    nginx -t

    echo "[RESINKIT] Enabling and restarting nginx"
    systemctl enable nginx || true
    systemctl restart nginx || true
    systemctl status nginx || true

    service nginx reload || true
    service nginx status || true

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.nginx_setup_completed
}

function debian_mount_s3_path() {
    # Skip setup if not running on EC2
    if [ "${IS_EC2:-false}" = "false" ]; then
        echo "[RESINKIT] IS_EC2 is false, skipping S3 mount setup"
        return 0
    fi

    # Use environment variables with fallbacks
    local BUCKET_NAME="${BUCKET_NAME:-resinkit-data}"
    local MOUNT_POINT="${MOUNT_POINT:-/mnt/resinkitdata}"

    # Check if s3 path is already mounted
    if mount | grep -q "$MOUNT_POINT"; then
        echo "[RESINKIT] $MOUNT_POINT already mounted, skipping"
        return 0
    fi

    # Check if UID environment variable is set
    if [ -z "$USER_ID" ]; then
        echo "[RESINKIT] Error: USER_ID environment variable is not set"
        exit 1
    fi

    # Check if mount-s3 is already installed
    if ! command -v mount-s3 >/dev/null 2>&1; then
        echo "[RESINKIT] Installing mount-s3..."

        # Detect architecture
        ARCH=$(dpkg --print-architecture)
        if [ "$ARCH" = "amd64" ]; then
            MOUNT_S3_ARCH="x86_64"
        elif [ "$ARCH" = "arm64" ]; then
            MOUNT_S3_ARCH="arm64"
        else
            echo "[RESINKIT] Error: Unsupported architecture: $ARCH"
            return 1
        fi

        # Download and install mount-s3
        wget https://s3.amazonaws.com/mountpoint-s3-release/latest/${MOUNT_S3_ARCH}/mount-s3.deb -O /tmp/mount-s3.deb
        apt-get update
        apt-get install -y /tmp/mount-s3.deb
        rm -f /tmp/mount-s3.deb
    else
        echo "[RESINKIT] mount-s3 is already installed"
    fi

    # Create mount point if it doesn't exist
    if [ ! -d "$MOUNT_POINT" ]; then
        echo "[RESINKIT] Creating mount point $MOUNT_POINT"
        mkdir -p "$MOUNT_POINT"
    fi

    # Check if already mounted
    if mount | grep -q "$MOUNT_POINT"; then
        echo "[RESINKIT] $MOUNT_POINT is already mounted"
    else
        echo "[RESINKIT] Mounting with command: mount-s3 s3://$BUCKET_NAME/$USER_ID/ $MOUNT_POINT"
        mount-s3 "s3://$BUCKET_NAME/$USER_ID/" "$MOUNT_POINT" || {
            echo "[RESINKIT] Error: Failed to mount S3 path"
            return 1
        }
        echo "[RESINKIT] Successfully mounted S3 path"
    fi

    # Add to fstab if not already present (mount-s3 fstab entry)
    local FSTAB_ENTRY="s3://$BUCKET_NAME/$USER_ID/ $MOUNT_POINT fuse.mount-s3 _netdev 0 0"
    if ! grep -q "$MOUNT_POINT" /etc/fstab; then
        echo "[RESINKIT] Adding mount to /etc/fstab for persistence"
        echo "$FSTAB_ENTRY" >>/etc/fstab
        echo "[RESINKIT] Added to fstab: $FSTAB_ENTRY"
    else
        echo "[RESINKIT] Mount point already exists in /etc/fstab"
    fi

    echo "[RESINKIT] S3 mount setup completed successfully"
}

function debian_install_genai_toolbox() {
    # Check if genai-toolbox is already installed
    if [ -f "/opt/setup/.genai_toolbox_installed" ]; then
        echo "[RESINKIT] genai-toolbox already installed, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing genai-toolbox"

    # Set version
    local GENAI_TOOLBOX_VERSION=${GENAI_TOOLBOX_VERSION:-0.9.0}
    # Download and install genai-toolbox
    wget "https://storage.googleapis.com/genai-toolbox/v${GENAI_TOOLBOX_VERSION}/linux/${GENAI_TOOLBOX_ARCH}/toolbox" -O ${GENAI_TOOLBOX_BIN}
    chmod +x ${GENAI_TOOLBOX_BIN}

    # Create a default tools.yaml if it doesn't exist
    mkdir -p ${GENAI_TOOLBOX_DIR}/
    if [ ! -f "${GENAI_TOOLBOX_TOOLS_YAML}" ]; then
        echo "[RESINKIT] Creating default tools.yaml configuration..."
        mkdir -p ${GENAI_TOOLBOX_DIR}
        cat >${GENAI_TOOLBOX_TOOLS_YAML} <<'EOF'
# Default genai-toolbox configuration
tools:
  - name: "echo"
    description: "Echo tool for testing"
    path: "/bin/echo"
EOF
    fi

    # Verify installation
    if [ -f "${GENAI_TOOLBOX_BIN}" ]; then
        echo "[RESINKIT] genai-toolbox installed successfully"
        ${GENAI_TOOLBOX_BIN} --version || echo "[RESINKIT] genai-toolbox version check failed"
    else
        echo "[RESINKIT] Error: genai-toolbox installation failed"
        return 1
    fi

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.genai_toolbox_installed
}

function debian_install_admin_tools() {
    apt update
    apt install -y curl jq lsof net-tools
}

function debian_install_all() {
    debian_install_common_packages
    debian_install_java
    debian_install_flink
    debian_install_gosu
    debian_install_kafka
    debian_install_flink_jars
    debian_install_jupyter
    debian_install_resinkit
    debian_install_nginx
    debian_mount_s3_path
    debian_install_genai_toolbox
    debian_install_admin_tools
    set +x
    echo "----------------------------------------"
    echo "[RESINKIT] ✅ Installation completed"
    echo "----------------------------------------"
}
