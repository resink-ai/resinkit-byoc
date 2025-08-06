"""Configuration management for resinkit-byoc."""

import os

from dotenv import find_dotenv, load_dotenv

from resinkit_byoc.core.find_root import find_project_root

# Import warnings filter to suppress non-critical container warnings
from . import warnings_filter  # noqa: F401

# Global flag to track if dotenvs have been loaded
_dotenvs_loaded = False


def load_dotenvs() -> None:
    """
    Load environment variables from .env files.

    Loads variables from:
    - .env.common
    - .env.{ENV} (where ENV defaults to 'dev')

    This function should be called once at application startup.
    """
    global _dotenvs_loaded

    if _dotenvs_loaded:
        return

    load_dotenv(find_dotenv(".env.common"))
    load_dotenv(find_dotenv(f".env.{os.getenv('ENV', 'dev')}"))

    _dotenvs_loaded = True
