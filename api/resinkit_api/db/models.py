from datetime import datetime
import enum
import json
from typing import Any, Dict, List

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
    func,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from resinkit_api.core.logging import get_logger

Base = declarative_base()

logger = get_logger(__name__)


class TaskStatus(enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    VALIDATING = "VALIDATING"
    PREPARING = "PREPARING"
    BUILDING = "BUILDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"

    @classmethod
    def from_str(cls, status: str) -> "TaskStatus":
        """Parse a status string to TaskStatus enum, fallback to FAILED if unknown."""
        try:
            # Special case: treat TIMEOUT as FAILED
            if status == "TIMEOUT":
                return cls.FAILED
            return cls[status]
        except (KeyError, TypeError):
            return cls.FAILED


class JSONString(TypeDecorator):
    """Custom type for JSON stored as string in SQLite"""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        try:
            return json.dumps(value)
        except Exception as e:
            logger.error(f"Error dumping JSON: {str(e)}", exc_info=True)
            return None

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


class Variable(Base):
    """Model for storing encrypted variables"""

    __tablename__ = "variables"

    name = Column(String, primary_key=True)
    encrypted_value = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )
    created_by = Column(String, nullable=False)

    # Define indexes
    __table_args__ = (Index("idx_variables_name", "name"),)


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True)
    task_type = Column(String, nullable=False)
    task_name = Column(String)
    description = Column(Text)
    status = Column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        server_default=text("'PENDING'"),
    )
    priority = Column(Integer, nullable=False, default=0, server_default=text("0"))
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    expires_at = Column(DateTime)
    submitted_configs = Column(JSONString, nullable=False)
    error_info = Column(JSONString)
    result_summary = Column(JSONString)
    execution_details = Column(JSONString)
    progress_details = Column(JSONString)
    created_by = Column(String, nullable=False)
    notification_config = Column(JSONString)
    tags = Column(JSONString)
    active = Column(Boolean, nullable=False, default=True, server_default=text("1"))

    # Define relationships
    events = relationship("TaskEvent", back_populates="task", cascade="all, delete-orphan")

    # Define CheckConstraint for status enum values
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'SUBMITTED', 'VALIDATING', 'PREPARING', 'BUILDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLING', 'CANCELLED')",
            name="valid_task_status",
        ),
        # Define indexes
        Index("idx_tasks_status", "status", sqlite_where=text("active = 1")),
        Index("idx_tasks_task_type", "task_type", sqlite_where=text("active = 1")),
        Index("idx_tasks_created_at", "created_at"),
        Index("idx_tasks_created_by", "created_by"),
        Index("idx_tasks_expires_at", "expires_at"),
    )

    # Helper methods for JSON fields
    def get_submitted_configs(self) -> Dict[str, Any]:
        return self.submitted_configs or {}

    def get_error_info(self) -> Dict[str, Any]:
        return self.error_info or {}

    def get_result_summary(self) -> Dict[str, Any]:
        return self.result_summary or {}

    def get_execution_details(self) -> Dict[str, Any]:
        return self.execution_details or {}

    def get_progress_details(self) -> Dict[str, Any]:
        return self.progress_details or {}

    def get_notification_config(self) -> Dict[str, Any]:
        return self.notification_config or {}

    def get_tags(self) -> List[str]:
        return self.tags or []


class TaskEvent(Base):
    __tablename__ = "task_events"

    event_id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.task_id"), nullable=False)
    event_type = Column(String, nullable=False)
    event_data = Column(JSONString)
    previous_status = Column(Enum(TaskStatus))
    new_status = Column(Enum(TaskStatus))
    timestamp = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.current_timestamp(),
    )
    actor = Column(String)

    # Define relationship back to Task
    task = relationship("Task", back_populates="events")

    # Define indexes
    __table_args__ = (
        Index("idx_task_events_task_id", "task_id"),
        Index("idx_task_events_timestamp", "timestamp"),
        Index("idx_task_events_event_type", "event_type"),
    )

    # Helper method for JSON field
    def get_event_data(self) -> Dict[str, Any]:
        return self.event_data or {}
