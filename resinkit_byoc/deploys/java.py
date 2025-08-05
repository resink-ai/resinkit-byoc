"""Install Java deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_java():
    """Install Java JDK 17 and Maven."""

    # Check if already installed
    marker_file = "/opt/setup/.java_installed"
    server.shell(
        name="Check if Java already installed",
        commands=[
            f'test -f {marker_file} && echo "[RESINKIT] Java already installed, skipping" && exit 0 || echo "[RESINKIT] Installing Java"'
        ],
    )

    # Get architecture (simplified approach)
    arch = "amd64"  # Default for most systems, could be dynamic if needed

    # Install OpenJDK 17
    apt.packages(
        name="Install OpenJDK 17",
        packages=["openjdk-17-jdk", "openjdk-17-jre"],
        present=True,
    )

    # Set Java alternatives
    server.shell(
        name="Set java alternative",
        commands=[
            f"update-alternatives --set java /usr/lib/jvm/java-17-openjdk-{arch}/bin/java"
        ],
    )

    server.shell(
        name="Set javac alternative",
        commands=[
            f"update-alternatives --set javac /usr/lib/jvm/java-17-openjdk-{arch}/bin/javac"
        ],
    )

    # Set JAVA_HOME environment variable
    server.shell(
        name="Set JAVA_HOME",
        commands=[f"export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-{arch}"],
    )

    # Install Maven
    apt.packages(
        name="Install Maven",
        packages=["maven"],
        present=True,
        extra_install_args="--no-install-recommends",
    )

    # Verify Maven installation
    server.shell(name="Verify Maven installation", commands=["mvn --version"])

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create Java marker", path=marker_file, present=True)
