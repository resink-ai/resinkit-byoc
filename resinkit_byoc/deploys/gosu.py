"""Install gosu deployment for resinkit-byoc."""

from pyinfra.operations import files, server


def install_gosu():
    """Install gosu for easy step-down from root."""

    # Check if already installed
    marker_file = "/opt/setup/.gosu_installed"
    server.shell(
        name="Check if gosu already installed",
        commands=[
            f'test -f /usr/local/bin/gosu && test -f {marker_file} && echo "[RESINKIT] gosu already installed, skipping" && exit 0 || echo "[RESINKIT] Installing gosu"'
        ],
    )

    # Set gosu version
    gosu_version = "1.17"

    # Get architecture (simplified)
    arch = "amd64"  # Default for most systems

    # Download gosu binary
    server.shell(
        name="Download gosu binary",
        commands=[
            f"wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu https://github.com/tianon/gosu/releases/download/{gosu_version}/gosu-{arch}"
        ],
    )

    # Download gosu signature
    server.shell(
        name="Download gosu signature",
        commands=[
            f"wget --retry-connrefused --waitretry=1 --tries=3 -O /usr/local/bin/gosu.asc https://github.com/tianon/gosu/releases/download/{gosu_version}/gosu-{arch}.asc"
        ],
    )

    # Make gosu executable
    files.file(name="Make gosu executable", path="/usr/local/bin/gosu", mode="755")

    # Verify gosu works
    server.shell(name="Verify gosu version", commands=["gosu --version"])

    server.shell(name="Test gosu functionality", commands=["gosu nobody true"])

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create gosu marker", path=marker_file, present=True)
