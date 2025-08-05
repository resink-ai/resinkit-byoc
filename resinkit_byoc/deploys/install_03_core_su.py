"""Install Flink deployment for resinkit-byoc."""

from resinkit_byoc.core.deploy_utils import run_script


def install_core_su():
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
