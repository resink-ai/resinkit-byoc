"""Install common packages deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_common_packages():
    """Install common packages required for resinkit-byoc."""

    # Check if already installed
    marker_file = "/opt/setup/.common_packages_installed"
    server.shell(
        name="Check if common packages already installed",
        commands=[
            f'test -f {marker_file} && echo "[RESINKIT] Common packages already installed, skipping" && exit 0 || echo "[RESINKIT] Installing common packages"'
        ],
    )

    # Set environment variables
    server.shell(
        name="Set timezone and frontend",
        commands=["export TZ=UTC && export DEBIAN_FRONTEND=noninteractive"],
    )

    # Update package list
    apt.update(name="Update package list")

    # Install basic packages
    basic_packages = [
        "vim",
        "wget",
        "gnupg",
        "nginx",
        "iputils-ping",
        "mariadb-client",
        "telnet",
        "ca-certificates",
        "git",
        "make",
        "curl",
        "zsh",
    ]

    apt.packages(
        name="Install basic packages",
        packages=basic_packages,
        present=True,
        extra_install_args="--no-install-recommends",
    )

    # Install development packages
    dev_packages = [
        "build-essential",
        "zlib1g-dev",
        "libncurses5-dev",
        "libgdbm-dev",
        "libnss3-dev",
        "libssl-dev",
        "libreadline-dev",
        "libffi-dev",
        "libsqlite3-dev",
        "libbz2-dev",
        "pkg-config",
        "liblzma-dev",
    ]

    apt.packages(
        name="Install development packages",
        packages=dev_packages,
        present=True,
        extra_install_args="--no-install-recommends",
    )

    # Install Python packages
    python_packages = [
        "python3",
        "python3-pip",
        "python3-dev",
        "python3-venv",
        "libpcre3-dev",
    ]

    apt.packages(name="Install Python packages", packages=python_packages, present=True)

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create common packages marker", path=marker_file, present=True)
