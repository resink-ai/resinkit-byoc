#!/bin/bash
# shellcheck disable=SC1091,SC2086,SC2046

: "${ROOT_DIR:?}" "${HADOOP_VERSION:?}" "${APACHE_HADOOP_URL:?}" "${FLINK_CDC_VER:?}" "${FLINK_VER_MINOR:?}" 

function _install_hadoop() {
    # Check if Hadoop is already installed
    if [ -d "/opt/hadoop" ] && [ -f "/opt/setup/.hadoop_installed" ]; then
        echo "[RESINKIT] Hadoop already installed, skipping"
        return 0
    fi

    echo "[RESINKIT] Installing Hadoop $HADOOP_VERSION for Iceberg integration (following official guide)"

    # Download and extract Hadoop as per Iceberg guide
    wget ${APACHE_HADOOP_URL}/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz -O /tmp/hadoop-${HADOOP_VERSION}.tar.gz
    tar xzvf /tmp/hadoop-${HADOOP_VERSION}.tar.gz -C /opt/
    mv /opt/hadoop-${HADOOP_VERSION} /opt/hadoop
    rm /tmp/hadoop-${HADOOP_VERSION}.tar.gz

    # Ensure proper permissions and ownership
    chown -R resinkit:resinkit /opt/hadoop 2>/dev/null || true
    chmod +x /opt/hadoop/bin/hadoop

    # Verify installation
    if [ -f "/opt/hadoop/bin/hadoop" ]; then
        echo "[RESINKIT] Hadoop installed successfully at /opt/hadoop"
        echo "[RESINKIT] Hadoop version: $(/opt/hadoop/bin/hadoop version | head -1)"
    else
        echo "[RESINKIT] Error: Hadoop installation failed"
        return 1
    fi

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.hadoop_installed
}


function _install_flink_jars() {
    # Check if Flink jars are already installed
    if [ -d "/opt/flink-cdc" ] && [ -f "/opt/setup/.flink_jars_installed" ]; then
        echo "[RESINKIT] Flink jars already installed, skipping"
        return 0
    fi

    FLINK_CDC_VER=${FLINK_CDC_VER:-3.4.0}
    # Download and extract Flink CDC if not already done
    if [ ! -d "/opt/flink-cdc" ]; then
        wget https://dlcdn.apache.org/flink/flink-cdc-${FLINK_CDC_VER}/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz -O /tmp/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz &&
            tar -xzf /tmp/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz -C /opt/ &&
            mv /opt/flink-cdc-${FLINK_CDC_VER} /opt/flink-cdc &&
            rm /tmp/flink-cdc-${FLINK_CDC_VER}-bin.tar.gz
    else
        echo "[RESINKIT] Flink CDC directory already exists, skipping extraction"
    fi

    # Download required JAR files if needed
    if [ $(find "/opt/flink/lib/" -name "*.jar" | wc -l) -lt 15 ]; then
        echo "[RESINKIT] 15 or fewer jars in /opt/flink/lib/, downloading"
        (
            cd "$ROOT_DIR/resources/flink/lib" || exit 1
            bash download.sh
            cp -v $ROOT_DIR/resources/flink/lib/flink/*.jar "/opt/flink/lib/"
        )
    else
        echo "[RESINKIT] 15 or more jars found in /opt/flink/lib/, skipping download"
    fi

    if [ $(find "/opt/flink-cdc/lib/" -name "*.jar" | wc -l) -lt 15 ]; then
        echo "[RESINKIT] 15 or fewer jars in /opt/flink-cdc/lib/, downloading"
        (
            cd "$ROOT_DIR/resources/flink/lib" || exit 1
            bash download.sh
            cp -v $ROOT_DIR/resources/flink/lib/cdc/*.jar "/opt/flink-cdc/lib/"
        )
    else
        echo "[RESINKIT] 15 or more jars found in /opt/flink-cdc/lib/, skipping download"
    fi

    # Copy plugins jars
    mkdir -p "/opt/flink/plugins/"
    if [ -d "$ROOT_DIR/resources/flink/lib/plugins/" ]; then
        echo "[RESINKIT] Copying plugins jars from $ROOT_DIR/resources/flink/lib/plugins/ to /opt/flink/plugins/"
        cp -rv "$ROOT_DIR/resources/flink/lib/plugins/" "/opt/flink/"
    else
        echo "[RESINKIT] No plugins jars found in $ROOT_DIR/resources/flink/lib/plugins/, skipping"
    fi

    # Copy configuration files
    mkdir -p "/opt/flink/conf/" "/opt/flink-cdc/conf/"
    cp -v "$ROOT_DIR/resources/flink/conf/conf.yaml" "/opt/flink/conf/config.yaml"
    cp -v "$ROOT_DIR/resources/flink/conf/log4j.properties" "/opt/flink/conf/log4j.properties"
    cp -rv "$ROOT_DIR/resources/flink/cdc/" "/opt/flink-cdc/conf/"

    # Set up /opt/flink/data/catalog-store
    mkdir -p "/opt/flink/data/catalog-store"
    cp -v "$ROOT_DIR/resources/flink/data/catalog-store/default_catalog.yaml" "/opt/flink/data/catalog-store/default_catalog.yaml"

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.flink_jars_installed
}

function _install_flink_entrypoint() {
    cp -v "$ROOT_DIR/resources/flink/flink_entrypoint.sh" "/home/resinkit/.local/bin/"
    chmod +x "/home/resinkit/.local/bin/flink_entrypoint.sh"
}

function install_flink() {
    # Check if Flink is already installed
    if [ -d "/opt/flink" ] && [ -f "/opt/setup/.flink_installed" ]; then
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
    export RESINKIT_ROLE=resinkit
    export RESINKIT_ROLE_HOME=/home/resinkit
    export FLINK_HOME=/opt/flink
    export PATH=$FLINK_HOME/bin:$PATH
    mkdir -p $FLINK_HOME

    cd "$FLINK_HOME" || exit 1

    wget -nv -O flink.tgz "$FLINK_TGZ_URL"

    tar -xf flink.tgz --strip-components=1
    rm flink.tgz

    

    # Copy rs_flink.sh to FLINK_HOME/bin/rs_flink.sh
    cp -v "$ROOT_DIR/resources/flink/bin/rs_flink.sh" "/opt/flink/bin/rs_flink.sh"
    chmod +x "/opt/flink/bin/rs_flink.sh"

    # Replace default REST/RPC endpoint bind address to use the container's network interface
    CONF_FILE="/opt/flink/conf/flink-conf.yaml"
    if [ ! -e "/opt/flink/conf/flink-conf.yaml" ]; then
        CONF_FILE="/opt/flink/conf/config.yaml"
        /bin/bash "/opt/flink/bin/config-parser-utils.sh" "/opt/flink/conf" "/opt/flink/bin" "/opt/flink/lib" \
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
    _install_hadoop

    _install_flink_jars

    chown -R resinkit:resinkit /opt/flink
    chown -R resinkit:resinkit /opt/flink-cdc
    chown -R resinkit:resinkit /home/resinkit

    # Create marker file
    mkdir -p /opt/setup
    touch /opt/setup/.flink_installed
}

install_flink