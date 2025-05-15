from datetime import datetime, UTC

from resinkit_api.db.models import Task

class TaskBase:
    def __init__(self, task_type: str, name: str = '', description: str = '', task_timeout_seconds: int = 3600, created_at: datetime = datetime.now(UTC)):
        # Extract common base fields
        self.task_type = task_type
        self.name = name
        self.description = description
        self.task_timeout_seconds = task_timeout_seconds
        self.created_at = created_at

        # Validate required fields
        if not self.task_type:
            raise ValueError("task_type is required")
        if not self.name:
            raise ValueError("name is required")
        
    @classmethod
    def from_config(cls, task_config: dict) -> 'TaskBase':
        return cls(task_config)
    
    @classmethod
    def from_dao(cls, task_dao: Task) -> 'TaskBase':
        return cls(task_dao.task_type, task_dao.name, task_dao.description, task_dao.task_timeout_seconds, task_dao.created_at)

    def expired(self) -> bool:
        return (datetime.now(UTC) - self.created_at).total_seconds() > self.task_timeout_seconds

    def has_ended(self) -> bool:
        return self.status == "FAILED" or self.status == "COMPLETED" or self.expired()
