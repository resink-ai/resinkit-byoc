from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from resinkit_api.db import tasks_crud
from resinkit_api.db.database import get_db
from resinkit_api.db.models import TaskStatus

router = APIRouter()


# Pydantic models for request/response validation
class TaskStatusEnum(str, Enum):
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


class TaskCreate(BaseModel):
    task_type: str
    task_name: Optional[str] = None
    description: Optional[str] = None
    priority: int = 0
    submitted_configs: Dict[str, Any]
    notification_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TaskEvent(BaseModel):
    event_id: int
    task_id: str
    event_type: str
    previous_status: Optional[TaskStatusEnum] = None
    new_status: Optional[TaskStatusEnum] = None
    timestamp: datetime
    actor: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class Task(BaseModel):
    task_id: str
    task_type: str
    task_name: Optional[str] = None
    description: Optional[str] = None
    status: TaskStatusEnum
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    submitted_configs: Dict[str, Any]
    error_info: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None
    execution_details: Optional[Dict[str, Any]] = None
    progress_details: Optional[Dict[str, Any]] = None
    created_by: str
    notification_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    active: bool
    events: Optional[List[TaskEvent]] = None

    class Config:
        orm_mode = True


class TaskStatusUpdate(BaseModel):
    status: TaskStatusEnum
    error_info: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None
    execution_details: Optional[Dict[str, Any]] = None
    progress_details: Optional[Dict[str, Any]] = None


@router.post("/tasks/", response_model=Task)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    created_by: str = Query("system", description="User ID or system identifier that created the task")
):
    """Create a new task."""
    return tasks_crud.create_task(
        db=db,
        task_type=task.task_type,
        task_name=task.task_name,
        description=task.description,
        priority=task.priority,
        submitted_configs=task.submitted_configs,
        notification_config=task.notification_config,
        tags=task.tags,
        created_by=created_by
    )


@router.get("/tasks/", response_model=List[Task])
def read_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatusEnum] = None,
    task_type: Optional[str] = None,
    created_by: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get a list of tasks with optional filtering."""
    # Convert string enum to actual enum if provided
    task_status = TaskStatus[status.name] if status else None
    
    tasks = tasks_crud.get_tasks(
        db=db,
        skip=skip,
        limit=limit,
        status=task_status,
        task_type=task_type,
        created_by=created_by,
        active_only=active_only
    )
    return tasks


@router.get("/tasks/{task_id}", response_model=Task)
def read_task(
    task_id: str = Path(..., description="The ID of the task to get"),
    db: Session = Depends(get_db)
):
    """Get a specific task by ID."""
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return db_task


@router.put("/tasks/{task_id}/status", response_model=Task)
def update_task_status(
    update: TaskStatusUpdate,
    task_id: str = Path(..., description="The ID of the task to update"),
    actor: Optional[str] = Query(None, description="User ID or system identifier making the update"),
    db: Session = Depends(get_db)
):
    """Update a task's status and related information."""
    # Convert string enum to actual enum
    new_status = TaskStatus[update.status.name]
    
    db_task = tasks_crud.update_task_status(
        db=db,
        task_id=task_id,
        new_status=new_status,
        actor=actor,
        error_info=update.error_info,
        result_summary=update.result_summary,
        execution_details=update.execution_details,
        progress_details=update.progress_details
    )
    
    if db_task is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return db_task


@router.delete("/tasks/{task_id}", response_model=bool)
def delete_task(
    task_id: str = Path(..., description="The ID of the task to delete"),
    db: Session = Depends(get_db)
):
    """Soft delete a task by setting active=False."""
    success = tasks_crud.delete_task(db=db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    return True


@router.get("/tasks/{task_id}/events", response_model=List[TaskEvent])
def read_task_events(
    task_id: str = Path(..., description="The ID of the task to get events for"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get events for a specific task."""
    # First check if the task exists
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")
    
    events = tasks_crud.get_task_events(db=db, task_id=task_id, skip=skip, limit=limit)
    return events 