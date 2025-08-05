"""Install nginx deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_nginx():
    """Install and configure nginx."""

    # Check if already installed
    marker_file = "/opt/setup/.nginx_installed"

    if files.get(path=marker_file):
        server.shell(
            name="Nginx already installed",
            command='echo "[RESINKIT] Nginx already installed, skipping"',
        )
        return

    # Install nginx (likely already installed with common packages)
    apt.packages(name="Install nginx", packages=["nginx"], present=True)

    # Copy nginx configuration
    server.shell(
        name="Copy nginx configuration",
        command="cp -v /root/resinkit-byoc/resources/nginx/nginx.conf /etc/nginx/nginx.conf",
        success_exit_codes=[0, 1],
    )

    # Enable and start nginx service
    server.shell(
        name="Enable nginx service",
        command="systemctl enable nginx",
        success_exit_codes=[0, 1],
    )

    server.shell(
        name="Start nginx service",
        command="systemctl start nginx",
        success_exit_codes=[0, 1],
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create nginx marker", path=marker_file, present=True)
