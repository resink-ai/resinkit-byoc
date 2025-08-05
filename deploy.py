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

from resinkit_byoc.deploys.admin_tools import install_admin_tools
from resinkit_byoc.deploys.flink_jars import install_flink_jars
from resinkit_byoc.deploys.install_00_prep import install_prep
from resinkit_byoc.deploys.install_01_core import install_core
from resinkit_byoc.deploys.install_02_flink import install_flink
from resinkit_byoc.deploys.jupyter import install_jupyter
from resinkit_byoc.deploys.mariadb import install_mariadb
from resinkit_byoc.deploys.python_uv import python_uv
from resinkit_byoc.deploys.resinkit import install_resinkit

# Export all deploy functions for direct access
__all__ = [
    "install_prep",
    "install_core",
    "install_flink",
    "install_flink_jars",
    "python_uv",
    "install_resinkit",
    "install_admin_tools",
    "install_mariadb",
    "install_jupyter",
]


def deploy_all():
    """Deploy all components."""
    install_prep()
    install_core()
