"""Install Java deployment for resinkit-byoc."""

import os

from pyinfra.operations import files, server

from resinkit_byoc.core.config import load_dotenvs


def post_install():
    """Post install tasks."""
    load_dotenvs()
    exp_vars = {}
    for k in [
        "FLINK_VER_MAJOR",
        "FLINK_VER_MINOR",
        "FLINK_CDC_VER",
        "FLINK_PAIMON_VER",
        "RESINKIT_API_SERVICE_PORT",
        "APACHE_HADOOP_URL",
        "HADOOP_VERSION",
        "MYSQL_RESINKIT_PASSWORD",
    ]:
        if k in os.environ:
            exp_vars[k] = os.getenv(k)

    # Render and install entrypoint.sh template
    files.template(
        src="resources/entrypoint.sh.j2",
        dest="/home/resinkit/.local/bin/entrypoint.sh",
        user="resinkit",
        group="resinkit",
        mode="755",
        jupyter_enabled=True,
        kafka_enabled=True,
        exp_vars=exp_vars,
        name="Install entrypoint.sh from template",
    )
    
    files.template(
        src="resources/env.exports.j2",
        dest="/home/resinkit/env.exports",
        user="resinkit",
        group="resinkit",
        mode="644",
        exp_vars=exp_vars,
        name="Install env.exports from template",
    )

    folders_to_chown = [
        "/opt/flink",
        "/opt/kafka",
        "/opt/resinkit",
        "/opt/resinkit/api",
        "/home/resinkit",
        "/var/log/resinkit",
    ]

    for folder in folders_to_chown:
        files.directory(
            path=folder,
            user="resinkit",
            group="resinkit",
            recursive=True,
            present=True,
            name=f"Create directory {folder}",
        )
        server.shell(
            commands=[f"chown -R resinkit:resinkit {folder}"],
            name=f"Change ownership of {folder} to resinkit:resinkit",
        )
