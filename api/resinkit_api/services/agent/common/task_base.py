import asyncio
from typing import Any, Optional

class PipelineTaskBase:
    def __init__(self, task_config: dict):
        self.task_config = task_config
        self.job_id: Optional[str] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file: Optional[str] = None
        self.status: str = "PENDING"
        self.result: Optional[Any] = None

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        raise NotImplementedError

    async def submit_job(self) -> str:
        raise NotImplementedError

    def get_status(self) -> str:
        raise NotImplementedError

    def get_result(self) -> Optional[Any]:
        raise NotImplementedError

    def get_log_summary(self, level: str = "INFO") -> str:
        raise NotImplementedError

    async def cancel(self, force: bool = False):
        raise NotImplementedError
