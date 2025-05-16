from datetime import datetime, UTC

from shortuuid import ShortUUID

from resinkit_api.db.models import Task, TaskStatus


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
        task_timeout_seconds: int = 3600,
        task_id: str = None,
        created_at: datetime = None,
    ):
        self.task_type = task_type
        self.name = name
        self.description = description
        self.task_timeout_seconds = task_timeout_seconds
        self.created_at = created_at or datetime.now(UTC)
        self.task_id = task_id or self.generate_task_id(self.task_type)
        self.status = TaskStatus.PENDING

    @classmethod
    def from_config(cls, task_config: dict) -> "TaskBase":
        cls.validate(task_config)
        return cls(
            task_type=task_config["task_type"],
            name=task_config["name"],
            description=task_config.get("description", ""),
            task_timeout_seconds=task_config.get("task_timeout_seconds", 3600),
            task_id=task_config.get("task_id"),
            created_at=task_config.get("created_at"),
        )

    @classmethod
    def from_dao(cls, task_dao: Task) -> "TaskBase":
        return cls(
            task_type=task_dao.task_type,
            name=task_dao.task_name,
            description=task_dao.description,
            task_timeout_seconds=task_dao.task_timeout_seconds,
            task_id=task_dao.task_id,
            created_at=task_dao.created_at,
        )

    def expired(self) -> bool:
        return (datetime.now(UTC) - self.created_at).total_seconds() > self.task_timeout_seconds

    def has_ended(self) -> bool:
        return (
            self.status == TaskStatus.FAILED or 
            self.status == TaskStatus.COMPLETED or 
            self.expired()
        )

    @classmethod
    def validate(cls, task_config: dict) -> None:
        if not task_config["task_type"]:
            raise ValueError("task_type is required")
        if not task_config["name"]:
            raise ValueError("name is required")
        if not task_config["task_id"]:
            raise ValueError("task_id is required")

