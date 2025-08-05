"""Install resinkit deployment for resinkit-byoc."""

from pyinfra.operations import files, server


def install_resinkit():
    """Install resinkit application."""

    # Check if already installed
    marker_file = "/opt/setup/.resinkit_installed"
    resinkit_path = "/opt/resinkit"

    if files.get(path=resinkit_path) and files.get(path=marker_file):
        server.shell(
            name="Resinkit already installed",
            command='echo "[RESINKIT] Resinkit already installed, skipping"',
        )
        return

    # Create resinkit directory
    files.directory(name="Create resinkit directory", path=resinkit_path, present=True)

    # Copy resinkit files (assuming they exist in the source)
    server.shell(
        name="Copy resinkit files",
        command="cp -r /root/resinkit-byoc/* /opt/resinkit/",
        success_exit_codes=[0, 1],
    )

    # Set ownership
    server.shell(
        name="Set resinkit ownership",
        command="chown -R resinkit:resinkit /opt/resinkit",
        success_exit_codes=[0, 1],
    )

    # Create Python virtual environment
    server.shell(
        name="Create Python venv for resinkit",
        command="cd /opt/resinkit && python3 -m venv .venv",
        success_exit_codes=[0, 1],
    )

    # Install Python dependencies
    server.shell(
        name="Install resinkit dependencies",
        command="cd /opt/resinkit && .venv/bin/pip install -r requirements.txt",
        success_exit_codes=[0, 1],
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create resinkit marker", path=marker_file, present=True)
