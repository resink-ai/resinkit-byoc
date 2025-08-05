"""Install Jupyter deployment for resinkit-byoc."""

from pyinfra.operations import files, server


def install_jupyter():
    """Install Jupyter notebook and related tools."""

    # Check if already installed
    marker_file = "/opt/setup/.jupyter_installed"

    if files.get(path=marker_file):
        server.shell(
            name="Jupyter already installed",
            command='echo "[RESINKIT] Jupyter already installed, skipping"',
        )
        return

    # Install Jupyter using pip3
    server.shell(
        name="Install Jupyter", command="pip3 install jupyter jupyterlab notebook"
    )

    # Install additional Python packages for data science
    server.shell(
        name="Install Python data science packages",
        command="pip3 install pandas numpy matplotlib seaborn plotly",
        success_exit_codes=[0, 1],
    )

    # Create Jupyter configuration directory
    files.directory(
        name="Create Jupyter config directory",
        path="/home/resinkit/.jupyter",
        present=True,
        user="resinkit",
        group="resinkit",
    )

    # Generate Jupyter configuration (optional)
    server.shell(
        name="Generate Jupyter config",
        command="su - resinkit -c 'jupyter notebook --generate-config'",
        success_exit_codes=[0, 1],
    )

    # Create setup directory and marker file
    files.directory(name="Create setup directory", path="/opt/setup", present=True)

    files.file(name="Create Jupyter marker", path=marker_file, present=True)
