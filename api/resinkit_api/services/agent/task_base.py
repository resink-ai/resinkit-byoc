from datetime import datetime, UTC
from typing import Any, Dict
from shortuuid import ShortUUID

from resinkit_api.db.models import Task, TaskStatus
from resinkit_api.utils.misc_utils import render_with_string_template


class TaskBase:
    @classmethod
    def generate_task_id(cls, task_type: str) -> str:
        """Generate a unique task ID for a given task type."""
        return f"{task_type.lower()}_{ShortUUID().random(length=9)}"

    def __init__(
        self,
        task_type: str,
        name: str,
        description: str = "",
        connection_timeout_seconds: int = 30,
        task_timeout_seconds: int = 3600,
        task_id: str = None,
        created_at: datetime = None,
        error_info: dict = None,
        result_summary: dict = None,
        execution_details: dict = None,
        progress_details: dict = None,
    ):
        self.task_type = task_type
        self.name = name
        self.description = description
        self.connection_timeout_seconds = connection_timeout_seconds
        self.task_timeout_seconds = task_timeout_seconds
        self.created_at = created_at or datetime.now(UTC)
        self.task_id = task_id or self.generate_task_id(self.task_type)
        self.status = TaskStatus.PENDING
        self.error_info = error_info or {}
        self.result_summary = result_summary or {}
        self.execution_details = execution_details or {}
        self.progress_details = progress_details or {}

    @classmethod
    def from_dao(cls, task_dao: Task, variables: Dict[str, Any] | None = None) -> "TaskBase":
        raise NotImplementedError

    def expired(self) -> bool:
        return (datetime.now(UTC) - self.created_at).total_seconds() > self.task_timeout_seconds

    def has_ended(self) -> bool:
        return self.status == TaskStatus.FAILED or self.status == TaskStatus.COMPLETED or self.expired()

    @classmethod
    def validate(cls, task_config: dict) -> None:
        # At base level, only task_type is required
        if not task_config["task_type"]:
            raise ValueError("task_type is required")

    def get_job_id(self) -> str | None:
        if not hasattr(self, "result") or not self.result:
            return None
        return self.result.get("job_id")

    @classmethod
    def render_with_variables(cls, submitted_configs: dict, variables: dict) -> Dict[str, Any]:
        return render_with_string_template(submitted_configs, variables)
