"""Install MariaDB deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_mariadb():
    """Install MariaDB server."""

    # Check if already installed
    marker_file = "/opt/setup/.mariadb_installed"

    if files.get(path=marker_file):
        server.shell(
            name="MariaDB already installed",
            command='echo "[RESINKIT] MariaDB already installed, skipping"',
        )
        return

    # Set non-interactive frontend
    server.shell(
        name="Set non-interactive frontend",
        command="export DEBIAN_FRONTEND=noninteractive",
    )

    # Install MariaDB server
    apt.packages(
        name="Install MariaDB server",
        packages=["mariadb-server", "mariadb-client"],
        present=True,
    )

    # Start and enable MariaDB service
    server.shell(
        name="Start MariaDB service",
        command="systemctl start mariadb",
        success_exit_codes=[0, 1],
    )

    server.shell(
        name="Enable MariaDB service",
        command="systemctl enable mariadb",
        success_exit_codes=[0, 1],
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create MariaDB marker", path=marker_file, present=True)
