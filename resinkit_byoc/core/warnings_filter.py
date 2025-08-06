"""Filter out known non-critical warnings."""

import sys
import warnings


def suppress_known_warnings():
    """Suppress known non-critical warnings that occur in containerized environments."""

    # Suppress threading warnings that occur with gevent/PyInfra in containers
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Redirect stderr to suppress thread exception messages
    if hasattr(sys, "_real_stderr"):
        return  # Already patched

    # Store original stderr
    sys._real_stderr = sys.stderr

    class FilteredStderr:
        def __init__(self, original_stderr):
            self.original = original_stderr

        def write(self, text):
            # Filter out known threading exception messages
            if any(
                msg in text
                for msg in [
                    "_DummyThread' object has no attribute '_handle'",
                    "Exception ignored in:",
                    "_after_fork",
                    "assert len(active) == 1",
                ]
            ):
                return  # Suppress these messages
            self.original.write(text)

        def flush(self):
            self.original.flush()

        def __getattr__(self, name):
            return getattr(self.original, name)

    # Replace stderr with filtered version
    sys.stderr = FilteredStderr(sys.stderr)


# Auto-apply when imported
suppress_known_warnings()
