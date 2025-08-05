"""Install Flink deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_flink():
    """Install Apache Flink."""

    # Check if already installed
    marker_file = "/opt/setup/.flink_installed"
    flink_home = "/opt/flink"

    if files.get(path=flink_home) and files.get(path=marker_file):
        server.shell(
            name="Flink already installed",
            command='echo "[RESINKIT] Flink already installed, skipping"',
        )
        return

    # Install required packages
    apt.packages(
        name="Install Flink dependencies",
        packages=["gpg", "libsnappy1v5", "gettext-base", "libjemalloc-dev"],
        present=True,
    )

    # Set Flink version
    flink_version = "1.20.1"

    # Download and extract Flink
    server.shell(
        name="Download Flink",
        command=f"wget https://dlcdn.apache.org/flink/flink-{flink_version}/flink-{flink_version}-bin-scala_2.12.tgz -O /tmp/flink.tgz",
    )

    files.directory(name="Create Flink directory", path=flink_home, present=True)

    server.shell(
        name="Extract Flink",
        command=f"tar -xzf /tmp/flink.tgz -C {flink_home} --strip-components=1",
    )

    server.shell(name="Remove Flink tarball", command="rm /tmp/flink.tgz")

    # Create resinkit user if it doesn't exist
    server.group(name="Create resinkit group", group="resinkit", gid=9999, system=True)

    server.user(
        name="Create resinkit user",
        user="resinkit",
        group="resinkit",
        home="/home/resinkit",
        create_home=True,
    )

    # Set ownership
    server.shell(
        name="Set Flink ownership", command="chown -R resinkit:resinkit /opt/flink"
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create Flink marker", path=marker_file, present=True)
