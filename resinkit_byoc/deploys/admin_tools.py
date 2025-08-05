"""Install admin tools deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_admin_tools():
    """Install administrative and debugging tools."""

    # Check if already installed
    marker_file = "/opt/setup/.admin_tools_installed"

    if files.get(path=marker_file):
        server.shell(
            name="Admin tools already installed",
            command='echo "[RESINKIT] Admin tools already installed, skipping"',
        )
        return

    # Install admin tools
    admin_packages = [
        "htop",
        "tree",
        "jq",
        "unzip",
        "zip",
        "rsync",
        "tcpdump",
        "netstat-nat",
        "lsof",
        "strace",
    ]

    apt.packages(
        name="Install admin tools",
        packages=admin_packages,
        present=True,
        success_exit_codes=[0, 100],  # Allow some packages to fail
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create admin tools marker", path=marker_file, present=True)
