import subprocess
from pathlib import Path

from dotenv import find_dotenv


def find_git_root() -> Path | None:
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        return Path(git_root)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def find_dotenv_path() -> Path | None:
    try:
        dotenv_path = find_dotenv(
            filename=".env.common", usecwd=True, raise_error_if_not_found=False
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    return Path(dotenv_path)


def find_project_root() -> Path:
    """
    Returns git root if it exists, otherwise parent of parent of .env.common
    """
    git_root = find_git_root()
    if git_root:
        return git_root
    else:
        dotenv_path = find_dotenv_path()
        if not dotenv_path:
            raise Exception("No .env.common file found")


if __name__ == "__main__":
    print("Project root:", find_project_root())
