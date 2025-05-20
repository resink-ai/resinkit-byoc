from typing import Dict, Any
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


# Custom exceptions for API error handling
class TaskError(Exception):
    pass


class InvalidTaskError(TaskError):
    pass


class TaskNotFoundError(TaskError):
    pass


class UnprocessableTaskError(TaskError):
    pass


class TaskConflictError(Exception):
    pass


# Pydantic model for task results
class TaskResult(BaseModel):
    task_id: str
    result_type: str
    data: Dict[str, Any]
    summary: str
