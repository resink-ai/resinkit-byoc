import os
import subprocess
from pathlib import Path

from dotenv import find_dotenv

# Cache for project root path
_project_root_cache = None


def find_git_root() -> Path | None:
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        return Path(git_root)
    except Exception as e:
        print(f"(find_git_root) An unexpected error occurred: {e}")
        return None


def find_dotenv_path() -> Path | None:
    try:
        dotenv_path = find_dotenv(filename=".env.common", usecwd=True, raise_error_if_not_found=False)
    except Exception as e:
        print(f"(find_dotenv_path) An unexpected error occurred: {e}")
        return None
    return Path(dotenv_path)


def find_project_root() -> Path:
    """
    Returns git root if it exists, otherwise parent of parent of .env.common
    The result is cached after the first call.
    """
    global _project_root_cache

    if _project_root_cache is not None:
        return _project_root_cache

    # 1. Use RESINKIT_API_PATH if set
    project_root = os.getenv("RESINKIT_API_PATH")
    if project_root:
        _project_root_cache = Path(project_root)
        return _project_root_cache

    # 2. Use .env.common path
    dotenv_path = find_dotenv_path()
    if dotenv_path:
        _project_root_cache = dotenv_path.parent
        return _project_root_cache

    # 3. Use git root
    git_root = find_git_root()
    if git_root:
        _project_root_cache = git_root
        return _project_root_cache

    raise Exception("project root not found")


if __name__ == "__main__":
    print("Project root:", find_project_root())
