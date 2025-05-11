import asyncio
from typing import Any, Optional


class TaskRunnerBase:
    def __init__(self, engine_config: dict | None = None):
        self.engine_config = engine_config or {}

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
