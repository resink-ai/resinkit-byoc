"""Install Java deployment for resinkit-byoc."""

from pyinfra.operations import files


def post_install():
    """Post install tasks."""

    exp_vars = {
        "JAVA_HOME": "/opt/java",
        "JUPYTER_ENABLED": False,
        "KAFKA_ENABLED": False,
        "FLINK_ENABLED": False,
        "RESINKIT_API_ENABLED": False,
    }
    # Render and install entrypoint.sh template
    files.template(
        src="resources/entrypoint.sh.j2",
        dest="/home/resinkit/.local/bin/entrypoint.sh",
        user="resinkit",
        group="resinkit",
        mode="755",
        jupyter_enabled=False,
        kafka_enabled=False,
        exp_vars={},
        name="Install entrypoint.sh from template",
    )
    
    folders_to_chown = [
        "/opt/flink",
        "/opt/kafka", 
        "/opt/resinkit",
        "/opt/resinkit/api",
        "/home/resinkit",
    ]
    
    for folder in folders_to_chown:
        files.directory(
            path=folder,
            user="resinkit",
            group="resinkit",
            recursive=True,
            name=f"Change ownership of {folder} to resinkit:resinkit"
        )
    
    # Ensure /home/resinkit/.local/bin directory exists
    files.directory(
        path="/home/resinkit/.local/bin",
        user="resinkit",
        group="resinkit",
        mode="755",
        name="Create /home/resinkit/.local/bin directory"
    )
    
