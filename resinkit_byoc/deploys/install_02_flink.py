"""Install Flink deployment for resinkit-byoc."""

from resinkit_byoc.core.deploy_utils import run_script


def install_flink():
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
