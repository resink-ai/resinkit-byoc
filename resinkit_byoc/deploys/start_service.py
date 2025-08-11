"""Start service for resinkit-byoc."""

from pyinfra.operations import server

def start_service():
    """Start service."""
    server.shell(
        name="Start service",
        commands=[
            "bash /home/resinkit/.local/bin/entrypoint.sh start",
            "bash /home/resinkit/.local/bin/entrypoint.sh status",
        ],
        _su_user="resinkit",
    )
