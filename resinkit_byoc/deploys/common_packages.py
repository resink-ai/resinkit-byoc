"""Install common packages deployment for resinkit-byoc."""

from pyinfra.operations import apt, files, server


def install_common_packages():
    """Install common packages required for resinkit-byoc."""

    # Check if already installed
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
