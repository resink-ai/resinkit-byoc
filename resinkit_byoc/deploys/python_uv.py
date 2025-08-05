"""Download Flink libraries using run_script deployment."""

import os

from resinkit_byoc.core.deploy_utils import run_script


def python_uv():
    """Install uv and python dependencies using the run_script utility."""

    run_script(
        "resources/setup_uv.sh",
        envs=["UV_INSTALL_DIR"],
        name=f"Install uv and python dependencies in {os.getenv('UV_INSTALL_DIR')}",
    )
