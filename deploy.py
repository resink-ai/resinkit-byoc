"""
PyInfra deployment entry point for resinkit-byoc.

This module provides packaged deploys that can be run individually:
    pyinfra @docker/ubuntu:22.04 deploy.install_common_packages
    pyinfra @docker/ubuntu:22.04 deploy.install_java
    pyinfra @docker/ubuntu:22.04 deploy.install_gosu
    pyinfra @docker/ubuntu:22.04 deploy.install_kafka
    etc.

Each deployment operation is implemented as a separate module under
the resinkit_byoc.deploys package.
"""

from resinkit_byoc.deploys.install_core import (
    install_01_core,
    install_03_flink,
    install_02_core_su,
)
from resinkit_byoc.deploys.install_extras import install_admin_tools, install_mariadb
from resinkit_byoc.deploys.pre_install import install_00_prep

# Export all deploy functions for direct access
__all__ = [
    "install_00_prep",
    "install_01_core",
    "install_03_flink",
    "install_02_core_su",
    "install_mariadb",
    "install_admin_tools",
]


def deploy_all():
    """Deploy all components."""
    install_00_prep()
    install_01_core()
    install_02_core_su()
    install_03_flink()
