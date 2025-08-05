"""Deploy utilities for resinkit-byoc."""

import os
from pathlib import Path
from typing import List, Optional

from pyinfra.operations import server

from .config import load_dotenvs
from .find_root import find_project_root


def run_script(
    script_path: str, envs: Optional[List[str]] = None, name: Optional[str] = None
) -> None:
    """
    Create a pyinfra deployment by reading a bash script and prefixing it with environment variables.

    Args:
        script_path: Relative path to the script from project root (e.g., 'resources/flink/lib/download.sh')
        envs: List of environment variable names to prefix the script with
        name: Optional name for the pyinfra operation (defaults to script filename)

    Example:
        run_script(
            'resources/flink/lib/download.sh',
            envs=['FLINK_HOME', 'FLINK_VER_MAJOR', 'FLINK_VER_MINOR', 'FLINK_CDC_VER']
        )
    """
    if envs is None:
        envs = []

    # Find project root
    project_root = find_project_root()

    # Construct full script path
    full_script_path = project_root / script_path

    if not full_script_path.exists():
        raise FileNotFoundError(f"Script not found: {full_script_path}")

    # Read the script content
    with open(full_script_path, "r") as f:
        script_content = f.read()

    # Ensure dotenvs are loaded
    load_dotenvs()

    # Build environment variable prefix
    env_prefix_lines = []
    for env_var in envs:
        # Get the value from os.environ (loaded from .env files)
        env_value = os.getenv(env_var)
        if env_value is not None:
            env_prefix_lines.append(f"export {env_var}='{env_value}'")
        else:
            # Add a comment for missing variables
            env_prefix_lines.append(f"# Warning: {env_var} not found in environment")

    # Combine environment variables with script content
    if env_prefix_lines:
        prefixed_script = "\\n".join(env_prefix_lines) + "\\n\\n" + script_content
    else:
        prefixed_script = script_content

    # Generate operation name
    if name is None:
        name = f"Run script: {Path(script_path).name}"

    # Execute the script using pyinfra
    server.shell(name=name, commands=[prefixed_script])
