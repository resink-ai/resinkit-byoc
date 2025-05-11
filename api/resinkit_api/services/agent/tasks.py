from typing import Optional
from shortuuid import ShortUUID
from sqlalchemy.orm import Session
from datetime import datetime

from resinkit_api.db import tasks_crud
from resinkit_api.db.database import get_db
from resinkit_api.db.models import TaskStatus


# Custom exceptions for API error handling
class InvalidTaskError(Exception):
    pass


class UnprocessableTaskError(Exception):
    pass


class TaskNotFoundError(Exception):
    pass


class TaskConflictError(Exception):
    pass


# 1. Submit a new Task
async def submit_task(payload: dict) -> dict:
    # Extract common base fields
    task_type = payload.get("task_type")
    name = payload.get("name")
    description = payload.get("description")

    # Validate required fields
    if not task_type:
        raise InvalidTaskError("task_type is required")
    if not name:
        raise InvalidTaskError("name is required")

    # Extract optional fields
    priority = payload.get("priority", 0)
    created_by = payload.get("created_by", "system")
    notification_config = payload.get("notification_config")
    tags = payload.get("tags")

    # Remove known fields from payload to isolate the submitted_configs
    known_fields = {"task_type", "name", "description", "priority", "created_by", "notification_config", "tags"}
    submitted_configs = {k: v for k, v in payload.items() if k not in known_fields}

    # Generate a unique task ID
    task_id = f"{task_type}-{ShortUUID().random(length=9)}"

    # Get database session
    db = next(get_db())
    try:
        # Create task in the database
        db_task = tasks_crud.create_task(
            db=db,
            task_id=task_id,
            task_type=task_type,
            task_name=name,
            description=description,
            priority=priority,
            submitted_configs=submitted_configs,
            created_by=created_by,
            notification_config=notification_config,
            tags=tags
        )

        # Return the task information
        return {
            "task_id": db_task.task_id,
            "task_type": db_task.task_type,
            "name": db_task.task_name,
            "description": db_task.description,
            "status": db_task.status.value,
            "message": f"Task '{name}' submitted successfully",
            "created_at": db_task.created_at.isoformat(),
            "_links": {"self": {"href": f"/api/v1/agent/tasks/{task_id}"}},
        }
    except Exception as e:
        db.rollback()
        raise UnprocessableTaskError(f"Failed to create task: {str(e)}")


# 2. Get Task Details
async def get_task_details(task_id: str) -> dict:
    # Get database session
    db = next(get_db())
    
    # Find the task in the database
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    
    if not db_task:
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
    # Convert the database model to a dictionary response
    return {
        "task_id": db_task.task_id,
        "task_type": db_task.task_type,
        "name": db_task.task_name,
        "description": db_task.description,
        "status": db_task.status.value,
        "priority": db_task.priority,
        "created_at": db_task.created_at.isoformat(),
        "updated_at": db_task.updated_at.isoformat(),
        "started_at": db_task.started_at.isoformat() if db_task.started_at else None,
        "finished_at": db_task.finished_at.isoformat() if db_task.finished_at else None,
        "submitted_configs": db_task.submitted_configs,
        "error_info": db_task.error_info,
        "result_summary": db_task.result_summary,
        "execution_details": db_task.execution_details,
        "progress_details": db_task.progress_details,
        "created_by": db_task.created_by,
        "notification_config": db_task.notification_config,
        "tags": db_task.tags,
        "_links": {"self": {"href": f"/api/v1/agent/tasks/{task_id}"}},
    }


# 3. List Tasks
async def list_tasks(
    task_type: Optional[str],
    status_: Optional[str],
    task_name_contains: Optional[str],
    tags_include_any: Optional[str],
    created_after: Optional[str],
    created_before: Optional[str],
    limit: Optional[int],
    page_token: Optional[str],
    sort_by: Optional[str],
    sort_order: Optional[str],
) -> dict:
    # Get database session
    db = next(get_db())
    
    # Process filters
    status = TaskStatus[status_] if status_ else None
    limit = limit or 100
    skip = 0  # TODO: Implement pagination with page_token
    
    # Convert date strings to datetime objects if provided
    created_after_date = datetime.fromisoformat(created_after) if created_after else None
    created_before_date = datetime.fromisoformat(created_before) if created_before else None
    
    # Query tasks with filters
    tasks = tasks_crud.get_tasks(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        task_type=task_type,
        created_after=created_after_date,
        created_before=created_before_date,
        task_name_contains=task_name_contains,
        tags_include_any=tags_include_any.split(",") if tags_include_any else None,
    )
    
    # Format response
    task_list = []
    for task in tasks:
        task_list.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "name": task.task_name,
            "description": task.description,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "_links": {"self": {"href": f"/api/v1/agent/tasks/{task.task_id}"}},
        })
    
    # TODO: Implement next_page_token based on pagination
    return {
        "tasks": task_list,
        "total_count": len(task_list),
        "next_page_token": None,
    }


# 4. Cancel a Task
async def cancel_task(task_id: str, payload: Optional[dict]) -> dict:
    # Get database session
    db = next(get_db())
    
    # Find the task in the database
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    
    if not db_task:
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
        
    # Can only cancel tasks that are in certain states
    cancellable_states = [
        TaskStatus.PENDING,
        TaskStatus.SUBMITTED, 
        TaskStatus.VALIDATING,
        TaskStatus.PREPARING,
        TaskStatus.BUILDING,
        TaskStatus.RUNNING
    ]
    
    if db_task.status not in cancellable_states:
        raise TaskConflictError(f"Cannot cancel task in {db_task.status.value} state")
    
    # Update task status to CANCELLING
    actor = payload.get("actor", "system") if payload else "system"
    
    db_task = tasks_crud.update_task_status(
        db=db,
        task_id=task_id,
        new_status=TaskStatus.CANCELLING,
        actor=actor,
    )
    
    return {
        "task_id": db_task.task_id,
        "status": db_task.status.value,
        "message": "Task cancellation initiated.",
        "_links": {"task_status": {"href": f"/api/v1/agent/tasks/{task_id}"}},
    }


# 5. Get Task Logs
async def get_task_logs(
    task_id: str,
    log_type: Optional[str],
    since_timestamp: Optional[str],
    since_token: Optional[str],
    limit_lines: Optional[int],
    log_level_filter: Optional[str],
) -> dict:
    # Get database session
    db = next(get_db())
    
    # Verify task exists
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    
    if not db_task:
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
    
    # TODO: Implement actual log retrieval logic
    limit = limit_lines or 100
    
    # Get task events that could serve as logs
    events = tasks_crud.get_task_events(db=db, task_id=task_id, limit=limit)
    
    log_entries = []
    for event in events:
        log_entries.append({
            "timestamp": event.timestamp.isoformat(),
            "log_type": "EVENT",
            "log_level": "INFO",
            "message": f"Event: {event.event_type}",
            "details": event.get_event_data(),
        })
    
    return {
        "task_id": task_id,
        "log_entries": log_entries,
        "next_log_token": None,
        "previous_log_token": None,
    }


async def stream_task_logs(
    task_id: str,
    log_type: Optional[str],
    since_timestamp: Optional[str],
    since_token: Optional[str],
    limit_lines: Optional[int],
    log_level_filter: Optional[str],
):
    # For now, just return the same as get_task_logs
    return await get_task_logs(
        task_id, log_type, since_timestamp, since_token, limit_lines, log_level_filter
    )


# 6. Get Task Results
async def get_task_results(task_id: str) -> dict:
    # Get database session
    db = next(get_db())
    
    # Find the task in the database
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    
    if not db_task:
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
    
    # Only completed tasks have results
    if db_task.status != TaskStatus.COMPLETED:
        raise UnprocessableTaskError(f"Task is in {db_task.status.value} state, not COMPLETED")
    
    return {
        "task_id": task_id,
        "result_type": "task_summary",
        "data": db_task.result_summary or {},
        "summary": "Task result data",
    }
