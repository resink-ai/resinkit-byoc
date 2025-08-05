"""Install Java deployment for resinkit-byoc."""

from resinkit_byoc.core.deploy_utils import run_script


def install_01_core():
    """Install Java JDK 17 and Maven."""
    run_script(
        "resinkit_byoc/scripts/install_core.sh",
        name="Install core components: Java, gosu, nginx, kafka",
        envs=["ROOT_DIR", "RESINKIT_ROLE"],
    )


def install_02_flink():
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


def install_03_core_su():
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
        _su_user="resinkit",
    )
