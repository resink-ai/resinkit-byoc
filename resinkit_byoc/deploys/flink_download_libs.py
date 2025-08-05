"""Download Flink libraries using run_script deployment."""

from resinkit_byoc.core.deploy_utils import run_script


def install_flink_libs():
    """Download and install Flink libraries using the run_script utility."""

    run_script(
        "resources/flink/lib/download.sh",
        envs=["FLINK_HOME", "FLINK_VER_MAJOR", "FLINK_VER_MINOR", "FLINK_CDC_VER"],
        name="Download Flink libraries",
    )
