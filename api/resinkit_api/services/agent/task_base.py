
from asyncio.subprocess import Process
from typing import Any, Optional

class TaskBase:
    def __init__(self, task_config: dict):
        # Extract common base fields
        self.task_type = task_config.get("task_type")
        self.name = task_config.get("name")
        self.description = task_config.get("description")

        # Validate required fields
        if not self.task_type:
            raise ValueError("task_type is required")
        if not self.name:
            raise ValueError("name is required")

        self.task_config = task_config
        self.job_id: Optional[str] = None
        self.process: Optional[Process] = None
        self.log_file: Optional[str] = None
        self.status: str = "PENDING"
        self.result: Optional[Any] = None

    def validate(self) -> None:
        raise NotImplementedError

