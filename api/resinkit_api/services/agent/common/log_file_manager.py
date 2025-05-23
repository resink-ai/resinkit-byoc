import os
import threading
from datetime import datetime
from typing import List

from structlog import BoundLogger

from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.data_models import LogEntry
from resinkit_api.utils.file_utils import tail


class LogFileManager:
    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    LEVEL_CRITICAL = "CRITICAL"

    def __init__(self, file_path: str, limit: int = 1000, logger: BoundLogger | None = None):
        self.file_path = file_path
        self.limit = limit
        self._lock = threading.Lock()
        self._buffer: List[LogEntry] = []
        self._load_existing()
        self.logger = logger or get_logger(__name__)

    def _load_existing(self):
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, "r") as f:
                lines = f.readlines()
            for line in lines[-self.limit :]:
                entry = self._parse_log_line(line)
                if entry:
                    self._buffer.append(entry)
        except Exception:
            pass

    def _write(self, level: str, message: str):
        timestamp = int(datetime.now().timestamp() * 1000)
        log_line = f"[{timestamp}] [{level}] {message}\n"
        entry = LogEntry(timestamp=timestamp, level=level, message=message)
        with self._lock:
            self._buffer.append(entry)
            if len(self._buffer) > self.limit:
                self._buffer = self._buffer[-self.limit :]
            with open(self.file_path, "a") as f:
                f.write(log_line)

    def info(self, message: str):
        self.logger.info(message)
        self._write(self.LEVEL_INFO, message)

    def warning(self, message: str):
        self.logger.warning(message)
        self._write(self.LEVEL_WARNING, message)

    def error(self, message: str):
        self.logger.error(message)
        self._write(self.LEVEL_ERROR, message)

    def critical(self, message: str):
        self.logger.critical(message)
        self._write(self.LEVEL_CRITICAL, message)

    def get_entries(self, level: str = None) -> List[LogEntry]:
        # Efficiently read only the last `limit` lines from the file (like tail -n $limit)
        with self._lock:
            lines = tail(self.file_path, self.limit)
        entries = []
        for line in lines:
            entry = self._parse_log_line(line)
            if entry:
                if level is None or entry.level == level:
                    entries.append(entry)
        return entries

    @staticmethod
    def _parse_log_line(line: str):
        import re

        # match f"[{timestamp}] [{level}] {message}\n"
        log_pattern = r"\[(\d+)\] \[(INFO|WARNING|ERROR|CRITICAL)\] (.*)"
        match = re.search(log_pattern, line)
        if match:
            timestamp, log_level, message = match.groups()
            return LogEntry(timestamp=timestamp, level=log_level, message=message.strip())
        return None
