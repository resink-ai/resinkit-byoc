import os


def tail(file_path: str, n: int) -> list[str]:
    """Read last n lines from file efficiently and return as list of strings."""
    avg_line_length = 150
    to_read = n * avg_line_length
    lines = []

    with open(file_path, "rb") as f:
        try:
            f.seek(-to_read, os.SEEK_END)
        except OSError:
            f.seek(0)
        lines = f.readlines()[-n:]
    # Decode each line from bytes to string
    return [line.decode("utf-8", errors="replace") for line in lines]
