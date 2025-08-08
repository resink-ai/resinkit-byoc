"""Install Java deployment for resinkit-byoc."""

import os
from pyinfra.operations import files, server

from resinkit_byoc.core.config import load_dotenvs
from resinkit_byoc.core.deploy_utils import run_script
from resinkit_byoc.core.find_root import find_project_root


def install_01_core():
    """Install Java JDK 17 and Maven."""
    run_script(
        "resinkit_byoc/scripts/install_core.sh",
        name="Install core components: Java, gosu, nginx, kafka",
        envs=["ROOT_DIR", "RESINKIT_API_GITHUB_TOKEN"],
    )


def install_02_core_su():
    """Install core components for su user."""

    run_script(
        "resinkit_byoc/scripts/install_core_su.sh",
        name="Install core components for su user",
        envs=[
            "ROOT_DIR",
            "HADOOP_VERSION",
            "APACHE_HADOOP_URL",
            "FLINK_CDC_VER",
            "FLINK_VER_MINOR",
        ],
    )


def install_03_flink():
    """Install Apache Flink."""

    run_script(
        "resinkit_byoc/scripts/install_flink.sh",
        name="Install Flink",
        envs=[
            "ROOT_DIR",
            "HADOOP_VERSION",
            "APACHE_HADOOP_URL",
            "FLINK_CDC_VER",
            "FLINK_VER_MINOR",
        ],
    )


def install_01_core_jupyter():
    """Install Jupyter components."""
    load_dotenvs()
    ROOT_DIR = os.getenv("ROOT_DIR")
    RESINKIT_ID = os.getenv("RESINKIT_ID")
    
    server.shell(
        name="Copy resinkit_sample_project to /home/resinkit/",
        commands=[
            f"cp -r {ROOT_DIR}/resources/jupyter/resinkit_sample_project /home/resinkit/",
        ],
    )
    
    # Render and install jupyter_entrypoint.sh from template
    files.template(
        name="Render jupyter_entrypoint.sh from template",
        src="resources/jupyter/jupyter_entrypoint.sh.j2",
        dest="/home/resinkit/.local/bin/jupyter_entrypoint.sh",
        user="resinkit",
        group="resinkit",
        mode="755",
        create_remote_dir=True,
        RESINKIT_ID=RESINKIT_ID,
    )
    
    # Change ownership of resinkit_sample_project to resinkit:resinkit
    server.shell(
        name="Change ownership of resinkit_sample_project to resinkit:resinkit",
        commands=["chown -R resinkit:resinkit /home/resinkit/resinkit_sample_project"],
    )
