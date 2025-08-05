"""Install Flink jars deployment for resinkit-byoc."""

from pyinfra.operations import files, server


def install_flink_jars():
    """Install Flink CDC and related jars."""

    # Check if already installed
    marker_file = "/opt/setup/.flink_jars_installed"
    flink_cdc_home = "/opt/flink-cdc"

    if files.get(path=flink_cdc_home) and files.get(path=marker_file):
        server.shell(
            name="Flink jars already installed",
            command='echo "[RESINKIT] Flink jars already installed, skipping"',
        )
        return

    # Set versions
    flink_cdc_version = "3.4.0"

    # Create CDC directory
    files.directory(
        name="Create Flink CDC directory", path=flink_cdc_home, present=True
    )

    # Download and install Flink CDC
    server.shell(
        name="Download Flink CDC",
        command=f"wget https://github.com/apache/flink-cdc/releases/download/release-{flink_cdc_version}/flink-cdc-{flink_cdc_version}-bin.tar.gz -O /tmp/flink-cdc.tar.gz",
    )

    server.shell(
        name="Extract Flink CDC",
        command=f"tar -xzf /tmp/flink-cdc.tar.gz -C {flink_cdc_home} --strip-components=1",
    )

    server.shell(name="Remove CDC tarball", command="rm /tmp/flink-cdc.tar.gz")

    # Set ownership
    server.shell(
        name="Set Flink CDC ownership",
        command="chown -R resinkit:resinkit /opt/flink-cdc",
        success_exit_codes=[0, 1],
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create Flink jars marker", path=marker_file, present=True)
