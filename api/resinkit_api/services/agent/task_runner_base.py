import asyncio
from typing import Any, Optional

from resinkit_api.services.agent.task_base import TaskBase


class TaskRunnerBase:
    def __init__(self, runtime_env: dict | None = None):
        self.runtime_env = runtime_env or {}

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        raise NotImplementedError

    async def submit_job(self, task_config: dict) -> TaskBase:
        raise NotImplementedError

    def get_status(self, task_id: str) -> str:
        raise NotImplementedError

    def get_result(self, task_id: str) -> Optional[Any]:
        raise NotImplementedError

    def get_log_summary(self, task_id: str, level: str = "INFO") -> str:
        raise NotImplementedError

    async def cancel(self, task_id: str, force: bool = False):
        raise NotImplementedError
