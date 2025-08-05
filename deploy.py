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
from resinkit_byoc.deploys.common_packages import install_common_packages
from resinkit_byoc.deploys.flink import install_flink
from resinkit_byoc.deploys.flink_jars import install_flink_jars
from resinkit_byoc.deploys.gosu import install_gosu
from resinkit_byoc.deploys.java import install_java
from resinkit_byoc.deploys.jupyter import install_jupyter
from resinkit_byoc.deploys.kafka import install_kafka
from resinkit_byoc.deploys.mariadb import install_mariadb
from resinkit_byoc.deploys.nginx import install_nginx
from resinkit_byoc.deploys.python_uv import python_uv
from resinkit_byoc.deploys.resinkit import install_resinkit

# Export all deploy functions for direct access
__all__ = [
    "install_common_packages",
    "install_java",
    "install_gosu",
    "install_kafka",
    "install_flink",
    "install_flink_jars",
    "python_uv",
    "install_resinkit",
    "install_nginx",
    "install_admin_tools",
    "install_mariadb",
    "install_jupyter",
]
