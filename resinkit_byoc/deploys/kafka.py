"""Install Kafka deployment for resinkit-byoc."""

from pyinfra.operations import files, server


def install_kafka():
    """Install Apache Kafka."""

    # Check if already installed
    marker_file = "/opt/setup/.kafka_installed"
    kafka_dir = "/opt/kafka"

    server.shell(
        name="Check if Kafka already installed",
        commands=[
            f'test -d {kafka_dir} && test -f {marker_file} && echo "[RESINKIT] Kafka already installed, skipping" && exit 0 || echo "[RESINKIT] Installing Kafka"'
        ],
    )

    # Download and extract Kafka
    server.shell(
        name="Download Kafka",
        commands=[
            "wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz"
        ],
    )

    server.shell(name="Extract Kafka", commands=["tar -xzf /tmp/kafka.tgz -C /opt"])

    server.shell(
        name="Move Kafka to final location",
        commands=["mv /opt/kafka_2.12-3.4.0 /opt/kafka"],
    )

    server.shell(name="Remove Kafka tarball", commands=["rm /tmp/kafka.tgz"])

    # Copy server properties configuration
    # Note: This assumes the kafka config exists in resources directory
    # You may need to adjust the path or create the config file separately
    server.shell(
        name="Copy Kafka server properties",
        commands=[
            "cp -v /root/resinkit-byoc/resources/kafka/server.properties /opt/kafka/config/server.properties || echo 'Config file not found, using defaults'"
        ],
    )

    # Create Kafka logs directory
    files.directory(
        name="Create Kafka logs directory", path="/opt/kafka/logs", present=True
    )

    # Set ownership and permissions
    server.shell(
        name="Set Kafka ownership",
        commands=[
            "chown -R ${RESINKIT_ROLE:-resinkit}:${RESINKIT_ROLE:-resinkit} /opt/kafka || echo 'User not found, skipping ownership change'"
        ],
    )

    server.shell(
        name="Set Kafka logs permissions", commands=["chmod -R 755 /opt/kafka/logs"]
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create Kafka marker", path=marker_file, present=True)
