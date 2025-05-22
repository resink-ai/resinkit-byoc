from typing import Any, Optional, List, Dict

from resinkit_api.db.models import Task
from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.services.agent.data_models import LogEntry


class TaskRunnerBase:
    def __init__(self, runtime_env: dict | None = None):
        self.runtime_env = runtime_env or {}

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        raise NotImplementedError

    def from_dao(self, dao: Task, variables: Dict[str, Any] | None = None) -> TaskBase:
        raise NotImplementedError

    async def submit_task(self, task: TaskBase) -> TaskBase:
        raise NotImplementedError

    def get_status(self, task: TaskBase) -> str:
        raise NotImplementedError

    def get_result(self, task: TaskBase) -> Optional[Any]:
        raise NotImplementedError

    def get_log_summary(self, task: TaskBase, level: str = "INFO") -> List[LogEntry]:
        raise NotImplementedError

    async def cancel(self, task: TaskBase, force: bool = False) -> TaskBase:
        raise NotImplementedError

    async def fetch_task_status(self, task: TaskBase) -> TaskBase:
        """
        Fetches the latest status of a task and returns an updated task instance.

        Args:
            task: The task instance to check status for

        Returns:
            An updated task instance with the latest status
        """
        raise NotImplementedError
