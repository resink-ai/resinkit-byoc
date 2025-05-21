from datetime import datetime, UTC, timedelta
import uuid
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from resinkit_api.core.logging import get_logger
from resinkit_api.db.models import Task, TaskEvent, TaskStatus

logger = get_logger(__name__)


# Tasks CRUD operations
def get_task(db: Session, task_id: str) -> Optional[Task]:
    """Get a task by ID."""
    return db.query(Task).filter(Task.task_id == task_id).first()


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    task_type: Optional[str] = None,
    created_by: Optional[str] = None,
    active_only: bool = True,
    task_name_contains: Optional[str] = None,
    tags_include_any: Optional[List[str]] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    sort_params: Optional[Dict[str, int]] = None,
) -> List[Task]:
    """Get a list of tasks with optional filtering."""
    query = db.query(Task)

    if active_only:
        query = query.filter(Task.active == True)

    if status:
        query = query.filter(Task.status == status)

    if task_type:
        query = query.filter(Task.task_type == task_type)

    if created_by:
        query = query.filter(Task.created_by == created_by)

    if task_name_contains:
        query = query.filter(Task.task_name.ilike(f"%{task_name_contains}%"))

    if created_after:
        query = query.filter(Task.created_at >= created_after)

    if created_before:
        query = query.filter(Task.created_at <= created_before)

    if tags_include_any and len(tags_include_any) > 0:
        # Note: This is a simplistic approach and may not work efficiently
        # with JSON stored as string. In a production system, this should
        # use proper JSON querying capabilities of the database.
        for tag in tags_include_any:
            query = query.filter(Task.tags.like(f"%{tag}%"))

    # Apply custom sorting if provided
    if sort_params:
        for field, direction in sort_params.items():
            if hasattr(Task, field):
                column = getattr(Task, field)
                if direction > 0:
                    query = query.order_by(column.asc())
                else:
                    query = query.order_by(column.desc())
    else:
        # Default sorting by created_at descending
        query = query.order_by(Task.created_at.desc())

    return query.offset(skip).limit(limit).all()


def create_task(
    db: Session,
    task_type: str,
    submitted_configs: Dict[str, Any],
    created_by: str,
    task_id: Optional[str] = None,
    task_name: Optional[str] = None,
    description: Optional[str] = None,
    priority: int = 0,
    notification_config: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
) -> Task:
    """Create a new task."""
    if not task_id:
        task_id = str(uuid.uuid4())

    # Calculate task expiry time based on timeout
    expires_at = None
    task_timeout_seconds = submitted_configs.get("task_timeout_seconds")
    if task_timeout_seconds:
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(seconds=int(task_timeout_seconds))

    db_task = Task(
        task_id=task_id,
        task_type=task_type,
        task_name=task_name,
        description=description,
        status=TaskStatus.PENDING,
        priority=priority,
        submitted_configs=submitted_configs,
        created_by=created_by,
        notification_config=notification_config,
        tags=tags,
        expires_at=expires_at,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    # Create a task creation event
    create_task_event(db=db, task_id=task_id, event_type="CREATED", new_status=TaskStatus.PENDING, actor=created_by)

    return db_task


def update_task_status(
    db: Session,
    task_id: str,
    new_status: TaskStatus,
    actor: Optional[str] = None,
    error_info: Optional[Dict[str, Any]] = None,
    result_summary: Optional[Dict[str, Any]] = None,
    execution_details: Optional[Dict[str, Any]] = None,
    progress_details: Optional[Dict[str, Any]] = None,
) -> Optional[Task]:
    """Update a task's status and related information."""
    db_task = get_task(db, task_id)
    if not db_task:
        logger.error(f"Task {task_id} not found")
        return None

    previous_status = db_task.status
    db_task.status = new_status
    db_task.updated_at = datetime.now(UTC)

    # Set timestamps based on status
    if new_status == TaskStatus.RUNNING and not db_task.started_at:
        db_task.started_at = datetime.now(UTC)

    if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
        db_task.finished_at = datetime.now(UTC)

    # Update task details if provided
    if error_info is not None:
        db_task.error_info = error_info

    if result_summary is not None:
        db_task.result_summary = result_summary

    if execution_details is not None:
        db_task.execution_details = execution_details

    if progress_details is not None:
        db_task.progress_details = progress_details

    db.commit()
    db.refresh(db_task)

    # Create a task status change event
    event_data = {}
    if error_info is not None:
        event_data["error_info"] = error_info
    if result_summary is not None:
        event_data["result_summary"] = result_summary

    create_task_event(
        db=db,
        task_id=task_id,
        event_type="STATUS_CHANGE",
        previous_status=previous_status,
        new_status=new_status,
        actor=actor,
        event_data=event_data if event_data else None,
    )

    return db_task


def delete_task(db: Session, task_id: str) -> bool:
    """Soft delete a task by setting active=False."""
    db_task = get_task(db, task_id)
    if not db_task:
        return False

    db_task.active = False
    db_task.updated_at = datetime.now(UTC)
    db.commit()
    return True


# Task Events CRUD operations
def get_task_events(db: Session, task_id: str, skip: int = 0, limit: int = 100) -> List[TaskEvent]:
    """Get events for a specific task."""
    return db.query(TaskEvent).filter(TaskEvent.task_id == task_id).order_by(TaskEvent.timestamp.desc()).offset(skip).limit(limit).all()


def create_task_event(
    db: Session,
    task_id: str,
    event_type: str,
    previous_status: Optional[TaskStatus] = None,
    new_status: Optional[TaskStatus] = None,
    actor: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
) -> TaskEvent:
    """Create a new task event."""
    db_event = TaskEvent(task_id=task_id, event_type=event_type, previous_status=previous_status, new_status=new_status, actor=actor, event_data=event_data)

    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def delete_task_events(db: Session, task_id: str) -> int:
    """
    Permanently delete all TaskEvent records for a given task_id.
    Returns the number of deleted events.
    """
    deleted = db.query(TaskEvent).filter(TaskEvent.task_id == task_id).delete()
    db.commit()
    return deleted
