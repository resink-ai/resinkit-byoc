"""Install MariaDB deployment for resinkit-byoc."""

from pyinfra.operations import apt

from resinkit_byoc.core.deploy_utils import run_script


def install_mariadb():
    """Install MariaDB server."""

    run_script(
        "resinkit_byoc/scripts/install_mariadb.sh",
        name="Install MariaDB",
        envs=["ROOT_DIR", "MYSQL_RESINKIT_PASSWORD"],
    )


def install_admin_tools():
    """Install administrative and debugging tools."""

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
