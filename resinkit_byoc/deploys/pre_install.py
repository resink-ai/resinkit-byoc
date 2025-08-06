"""Install common packages deployment for resinkit-byoc."""

import os

from pyinfra.operations import apt, server
from resinkit_byoc.core.deploy_utils import run_script


def install_00_prep():
    """Install common packages and prepare for installation."""

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
        "git-lfs",
        "make",
        "curl",
        "zsh",
        "zip",
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

    # add resinkit user
    resinkit_role = os.getenv("RESINKIT_ROLE", "resinkit")
    server.user(
        name="Ensure resinkit user exists",
        user=resinkit_role,
        home=f"/home/{resinkit_role}",
        create_home=True,
    )

    run_script(
        "resinkit_byoc/scripts/pre_install.sh",
        name="Ensure resinkit-byoc repo exists",
        envs=["ROOT_DIR", "RESINKIT_BYOC_RELEASE_BRANCH"],
    )
