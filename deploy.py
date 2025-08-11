"""
PyInfra deployment entry point for resinkit-byoc.

This module provides packaged deploys that can be run individually:
    pyinfra @docker/ubuntu:22.04 deploy.install_00_prep
    pyinfra @docker/ubuntu:22.04 deploy.install_01_core
    etc.

Each deployment operation is implemented as a separate module under
the resinkit_byoc.deploys package.
"""

from resinkit_byoc.deploys.install_core import (
    install_01_core,
    install_011_core_jupyter,
    install_012_core_resinkit_api,
    install_02_core_su,
    install_03_flink,
)
from resinkit_byoc.deploys.install_extras import install_admin_tools, install_mariadb
from resinkit_byoc.deploys.post_install import post_install
from resinkit_byoc.deploys.pre_install import install_00_prep
from resinkit_byoc.deploys.start_service import start_service

# Export all deploy functions for direct access
__all__ = [
    "install_00_prep",
    "install_01_core",
    "install_011_core_jupyter",
    "install_012_core_resinkit_api",
    "install_02_core_su",
    "install_03_flink",
    "post_install",
    "install_mariadb",
    "install_admin_tools",
    "start_service",
]


def deploy_all():
    """Deploy all components."""
    install_00_prep()
    install_01_core()
    install_011_core_jupyter()
    install_012_core_resinkit_api()
    install_02_core_su()
    install_03_flink()
    post_install()

def start():
    """Start service."""
    start_service()


def all_in_one():
    """Deploy all components and start service."""
    deploy_all()
    start()
