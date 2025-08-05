"""Install Java deployment for resinkit-byoc."""

from resinkit_byoc.core.deploy_utils import run_script


def install_core():
    """Install Java JDK 17 and Maven."""
    run_script(
        "resinkit_byoc/scripts/install_core.sh",
        name="Install core components: Java, gosu, nginx, kafka",
        envs=["ROOT_DIR", "RESINKIT_ROLE"],
    )
