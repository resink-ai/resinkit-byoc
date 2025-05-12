from typing import Any, Optional
from shortuuid import ShortUUID
from datetime import datetime, UTC
import asyncio

from resinkit_api.db import tasks_crud
from resinkit_api.db.database import get_db
from resinkit_api.db.models import TaskStatus
from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.runner_registry import get_runner_for_task_type
from resinkit_api.services.agent import get_job_manager, get_sql_gateway

logger = get_logger(__name__)


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

    # Generate a unique task ID
    task_id = f"{task_type}_{ShortUUID().random(length=9)}"

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
            submitted_configs=payload,
            created_by=created_by,
            notification_config=notification_config,
            tags=tags
        )

        # Attempt to start executing the task asynchronously
        asyncio.create_task(execute_task(task_id))

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
        logger.error(f"Failed to create task: {str(e)}")
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
async def cancel_task(task_id: str, force: bool = False) -> dict:
    """
    Cancel a running task.
    
    Args:
        task_id: ID of the task to cancel
        force: Whether to force cancel the task
        
    Returns:
        A dict with cancellation result
    """
    # Get database session
    db = next(get_db())
    
    # Find the task in the database
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    
    if not db_task:
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
    
    # Verify that the task is in a cancellable state
    if db_task.status not in [TaskStatus.PENDING, TaskStatus.VALIDATING, TaskStatus.PREPARING, TaskStatus.RUNNING]:
        raise TaskConflictError(f"Task is not in a cancellable state. Current status: {db_task.status.value}")
    
    try:
        # Update status to CANCELLING
        tasks_crud.update_task_status(
            db=db,
            task_id=task_id,
            new_status=TaskStatus.CANCELLING,
            actor="user"
        )
        
        # Get the job ID from execution details
        job_id = None
        execution_details = db_task.get_execution_details()
        if execution_details and "job_id" in execution_details:
            job_id = execution_details["job_id"]
        
        if job_id:
            # Get the appropriate runner for this task type
            runner = get_runner_for_task_type(db_task.task_type)
            
            # Cancel the job in the runner
            await runner.cancel(job_id, force=force)
            
            # Update task status to CANCELLED
            tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.CANCELLED,
                actor="user"
            )
            
            return {
                "task_id": task_id,
                "success": True,
                "message": "Task cancelled successfully"
            }
        else:
            # If no job ID, just mark as cancelled
            tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.CANCELLED,
                actor="user"
            )
            
            return {
                "task_id": task_id,
                "success": True,
                "message": "Task marked as cancelled"
            }
    
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
        
        # Update with error info
        error_info = {
            "error": f"Failed to cancel: {str(e)}",
            "error_type": e.__class__.__name__,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        try:
            tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.FAILED,
                actor="system",
                error_info=error_info
            )
        except:
            pass
            
        raise UnprocessableTaskError(f"Failed to cancel task: {str(e)}")


# 5. Get Task Logs
async def get_task_logs(task_id: str, level: str = "INFO") -> str:
    """
    Get logs for a task.
    
    Args:
        task_id: ID of the task
        level: Log level to filter by
        
    Returns:
        A string containing the logs
        
    Raises:
        TaskNotFoundError: If the task is not found
    """
    db = next(get_db())
    
    # Find the task in the database
    db_task = tasks_crud.get_task(db=db, task_id=task_id)
    
    if not db_task:
        raise TaskNotFoundError(f"Task with ID {task_id} not found")
    
    try:
        # Get the job ID from execution details
        job_id = None
        execution_details = db_task.get_execution_details()
        if execution_details and "job_id" in execution_details:
            job_id = execution_details["job_id"]
        
        if job_id:
            # Get the appropriate runner for this task type
            runner = get_runner_for_task_type(db_task.task_type)
            
            # Get logs from the runner
            return runner.get_log_summary(job_id, level=level)
        else:
            return "No logs available - task hasn't been submitted to a runner yet"
    
    except Exception as e:
        logger.error(f"Failed to get logs for task {task_id}: {str(e)}")
        return f"Error retrieving logs: {str(e)}"


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


# 7. Execute a task
async def execute_task(task_id: str) -> None:
    """
    Execute a task using the appropriate runner.
    This function should be called asynchronously.
    
    Args:
        task_id: ID of the task to execute
    """
    db = next(get_db())
    
    try:
        # Get the task from the database
        db_task = tasks_crud.get_task(db=db, task_id=task_id)
        if not db_task:
            logger.error(f"Task not found: {task_id}")
            return
        
        # Update task status to VALIDATING
        db_task = tasks_crud.update_task_status(
            db=db,
            task_id=task_id,
            new_status=TaskStatus.VALIDATING,
            actor="system"
        )
        
        # Get the appropriate runner for this task type
        try:
            runner = get_runner_for_task_type(db_task.task_type)
        except ValueError as e:
            # If no runner is registered for this task type, mark the task as failed
            error_info = {
                "error": str(e),
                "error_type": "ValueError",
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.FAILED,
                actor="system",
                error_info=error_info
            )
            logger.error(f"Failed to execute task {task_id}: {str(e)}")
            return
        
        try:
            # Validate the task configuration
            runner.validate_config(db_task.submitted_configs)
            
            # Update task status to PREPARING
            db_task = tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.PREPARING,
                actor="system"
            )
            
            # Submit the job to the runner
            task_base = await runner.submit_job(db_task.submitted_configs)
            
            # Update task status to RUNNING and include execution details
            execution_details = {
                "job_id": task_base.job_id,
                "log_file": task_base.log_file
            }
            
            if hasattr(task_base, "execution_details"):
                execution_details.update(task_base.execution_details)
                
            db_task = tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.RUNNING,
                actor="system",
                execution_details=execution_details
            )
            
            # Start background monitoring of the task
            asyncio.create_task(monitor_task(task_id, runner, task_base.job_id))
            
        except Exception as e:
            # If validation or execution fails, mark the task as failed
            error_info = {
                "error": str(e),
                "error_type": e.__class__.__name__,
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.FAILED,
                actor="system",
                error_info=error_info
            )
            logger.error(f"Failed to execute task {task_id}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error executing task {task_id}: {str(e)}")


# 8. Monitor a running task
async def monitor_task(task_id: str, runner: Any, job_id: str) -> None:
    """
    Monitor a running task and update its status in the database.
    
    Args:
        task_id: ID of the task being monitored
        runner: The task runner instance
        job_id: ID of the job within the runner
    """
    db = next(get_db())
    
    try:
        # Poll for status periodically
        while True:
            # Get the current status from the runner
            status = runner.get_status(job_id)
            
            # Map status from runner to TaskStatus
            # This mapping might need adjustment depending on the runner implementation
            db_status = None
            if status == "RUNNING":
                db_status = TaskStatus.RUNNING
            elif status == "COMPLETED":
                db_status = TaskStatus.COMPLETED
            elif status == "FAILED":
                db_status = TaskStatus.FAILED
            elif status == "CANCELLED":
                db_status = TaskStatus.CANCELLED
            elif status == "CANCELLING":
                db_status = TaskStatus.CANCELLING
            
            # If we have a status to update, do it
            if db_status:
                # Get the result if the task has completed
                result_summary = None
                error_info = None
                
                if db_status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    result_data = runner.get_result(job_id)
                    if result_data:
                        if db_status == TaskStatus.COMPLETED:
                            result_summary = {
                                "success": True,
                                "result": result_data
                            }
                        else:
                            error_info = {
                                "error": str(result_data),
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                
                # Get logs for the task
                try:
                    log_summary = runner.get_log_summary(job_id)
                    execution_details = {
                        "log_summary": log_summary
                    }
                except:
                    execution_details = {}
                
                # Update task status in the database
                tasks_crud.update_task_status(
                    db=db,
                    task_id=task_id,
                    new_status=db_status,
                    actor="system",
                    result_summary=result_summary,
                    error_info=error_info,
                    execution_details=execution_details
                )
                
                # If the task has reached a terminal state, stop monitoring
                if db_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    break
            
            # Sleep before polling again
            await asyncio.sleep(5)
    
    except Exception as e:
        logger.error(f"Error monitoring task {task_id}: {str(e)}")
        # Make sure the task is marked as failed
        try:
            tasks_crud.update_task_status(
                db=db,
                task_id=task_id,
                new_status=TaskStatus.FAILED,
                actor="system",
                error_info={
                    "error": f"Monitoring error: {str(e)}",
                    "error_type": e.__class__.__name__,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )
        except Exception as inner_e:
            logger.error(f"Failed to update task status: {str(inner_e)}")
