from typing import Optional
from datetime import datetime, UTC
import asyncio

from resinkit_api.db import tasks_crud
from resinkit_api.db.database import get_db
from resinkit_api.db.models import Task, TaskStatus
from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.runner_registry import get_runner_for_task_type
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase
from resinkit_api.services.agent.task_base import TaskBase

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


class TaskManager:
    def __init__(self):
        self.polling_interval = 5  # Task monitoring poll interval in seconds
        self._monitoring_tasks = {}  # Track active monitoring tasks
        logger.info("TaskManager initialized with polling interval: %s seconds", self.polling_interval)

    async def submit_task(self, payload: dict) -> dict:
        TaskBase.validate(payload)

        # Extract common base fields
        task_type = payload.get("task_type")
        name = payload.get("name")
        description = payload.get("description")

        # Extract optional fields
        priority = payload.get("priority", 0)
        created_by = payload.get("created_by", "system")
        notification_config = payload.get("notification_config")
        tags = payload.get("tags")

        # Generate a unique task ID using TaskBase
        task_id = TaskBase.generate_task_id(task_type)
        payload["task_id"] = task_id  # Ensure payload carries the generated task_id
        logger.info("Generated task_id: %s for task type: %s", task_id, task_type)

        # Get database session
        db = next(get_db())
        try:
            # Create task in the database
            logger.debug("Creating task in database: task_id=%s", task_id)
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
                tags=tags,
            )
            logger.info("Task created in database: task_id=%s, status=%s", task_id, db_task.status.value)

            # Attempt to start executing the task asynchronously
            logger.debug("Scheduling asynchronous execution for task_id=%s", task_id)
            asyncio.create_task(self.execute_task(task_id))

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
            logger.error(f"Failed to create task: {str(e)}", exc_info=True)
            raise UnprocessableTaskError(f"Failed to create task: {str(e)}")

    async def get_task_details(self, task_id: str) -> dict:
        logger.info("Getting details for task_id=%s", task_id)

        # Get database session
        db = next(get_db())

        # Find the task in the database
        db_task: Task = tasks_crud.get_task(db=db, task_id=task_id)

        if not db_task:
            logger.warning("Task not found: task_id=%s", task_id)
            raise TaskNotFoundError(f"Task with ID {task_id} not found")

        logger.debug("Retrieved task details: task_id=%s, status=%s", task_id, db_task.status.value)
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
            "expires_at": db_task.expires_at.isoformat() if db_task.expires_at else None,
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

    async def list_tasks(
        self,
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
        logger.info("Listing tasks with filters: type=%s, status=%s, limit=%s", task_type, status_, limit)

        # Get database session
        db = next(get_db())

        # Process filters
        status = TaskStatus[status_] if status_ else None
        limit = limit or 100
        skip = 0  # TODO: Implement pagination with page_token

        # Convert date strings to datetime objects if provided
        created_after_date = datetime.fromisoformat(created_after) if created_after else None
        created_before_date = datetime.fromisoformat(created_before) if created_before else None

        logger.debug("Querying tasks with filters: status=%s, type=%s, name_contains=%s, tags=%s", status, task_type, task_name_contains, tags_include_any)

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

        logger.info("Found %d tasks matching filters", len(tasks))

        # Format response
        task_list = []
        for task in tasks:
            task_list.append(
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "name": task.task_name,
                    "description": task.description,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "expires_at": task.expires_at.isoformat() if task.expires_at else None,
                    "_links": {"self": {"href": f"/api/v1/agent/tasks/{task.task_id}"}},
                }
            )

        # TODO: Implement next_page_token based on pagination
        return {
            "tasks": task_list,
            "total_count": len(task_list),
            "next_page_token": None,
        }

    async def cancel_task(self, task_id: str, force: bool = False) -> dict:
        """
        Cancel a running task.

        Args:
            task_id: ID of the task to cancel
            force: Whether to force cancel the task

        Returns:
            A dict with cancellation result
        """
        logger.info("Attempting to cancel task: task_id=%s, force=%s", task_id, force)

        # Get database session
        db = next(get_db())

        # Find the task in the database
        db_task = tasks_crud.get_task(db=db, task_id=task_id)

        if not db_task:
            logger.warning("Cannot cancel: Task not found: task_id=%s", task_id)
            raise TaskNotFoundError(f"Task with ID {task_id} not found")

        # Verify that the task is in a cancellable state
        if db_task.status not in [TaskStatus.PENDING, TaskStatus.VALIDATING, TaskStatus.PREPARING, TaskStatus.RUNNING]:
            logger.warning("Cannot cancel: Task is in non-cancellable state: task_id=%s, status=%s", task_id, db_task.status.value)
            raise TaskConflictError(f"Task is not in a cancellable state. Current status: {db_task.status.value}")

        try:
            # Update status to CANCELLING
            logger.info("Updating task status to CANCELLING: task_id=%s", task_id)
            tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.CANCELLING, actor="user")

            # Get the appropriate runner for this task type
            logger.debug("Getting runner for task_type=%s", db_task.task_type)
            runner = get_runner_for_task_type(db_task.task_type)

            # Cancel the task in the runner using task_id
            logger.info("Cancelling task in runner: task_id=%s, force=%s", task_id, force)
            await runner.cancel(runner.from_dao(db_task), force=force)

            # Update task status to CANCELLED
            logger.info("Updating task status to CANCELLED: task_id=%s", task_id)
            tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.CANCELLED, actor="user")

            return {"task_id": task_id, "success": True, "message": "Task cancelled successfully"}

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}", exc_info=True)

            # Update with error info
            error_info = {"error": f"Failed to cancel: {str(e)}", "error_type": e.__class__.__name__, "timestamp": datetime.now(UTC).isoformat()}

            try:
                logger.info("Updating task status to FAILED after cancel error: task_id=%s", task_id)
                tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.FAILED, actor="system", error_info=error_info)
            except Exception as inner_e:
                logger.error(f"Failed to update task status: {str(inner_e)}", exc_info=True)

            raise UnprocessableTaskError(f"Failed to cancel task: {str(e)}")

    async def get_task_logs(
        self,
        task_id: str,
        log_type: Optional[str] = None,
        since_timestamp: Optional[str] = None,
        since_token: Optional[str] = None,
        limit_lines: Optional[int] = None,
        log_level_filter: Optional[str] = "INFO",
    ) -> str:
        """
        Get logs for a task.

        Args:
            task_id: ID of the task
            log_type: Type of logs to retrieve
            since_timestamp: Only get logs after this timestamp
            since_token: Continuation token for pagination
            limit_lines: Maximum number of log lines to retrieve
            log_level_filter: Log level to filter by

        Returns:
            A string containing the logs

        Raises:
            TaskNotFoundError: If the task is not found
        """
        logger.info("Getting logs for task: task_id=%s, log_type=%s, level=%s", task_id, log_type, log_level_filter)

        db = next(get_db())

        # Find the task in the database
        db_task: Task = tasks_crud.get_task(db=db, task_id=task_id)

        if not db_task:
            logger.warning("Cannot get logs: Task not found: task_id=%s", task_id)
            raise TaskNotFoundError(f"Task with ID {task_id} not found")

        try:
            logger.debug("Fetching logs from runner for task_id=%s", task_id)
            runner = get_runner_for_task_type(db_task.task_type)
            return runner.get_log_summary(runner.from_dao(db_task), level=log_level_filter)
        except Exception as e:
            logger.error(f"Failed to get logs for task {task_id}: {str(e)}", exc_info=True)
            return f"Error retrieving logs: {str(e)}"

    async def stream_task_logs(
        self,
        task_id: str,
        log_type: Optional[str],
        since_timestamp: Optional[str],
        since_token: Optional[str],
        limit_lines: Optional[int],
        log_level_filter: Optional[str],
    ):
        logger.info("Streaming logs for task: task_id=%s, log_type=%s", task_id, log_type)
        # For now, just return the same as get_task_logs
        return await self.get_task_logs(task_id, log_type, since_timestamp, since_token, limit_lines, log_level_filter)

    async def get_task_results(self, task_id: str) -> dict:
        logger.info("Getting results for task: task_id=%s", task_id)

        # Get database session
        db = next(get_db())

        # Find the task in the database
        db_task: Task = tasks_crud.get_task(db=db, task_id=task_id)

        if not db_task:
            logger.warning("Cannot get results: Task not found: task_id=%s", task_id)
            raise TaskNotFoundError(f"Task with ID {task_id} not found")

        # Only completed tasks have results
        if db_task.status != TaskStatus.COMPLETED:
            logger.warning("Cannot get results: Task not completed: task_id=%s, status=%s", task_id, db_task.status.value)
            raise UnprocessableTaskError(f"Task is in {db_task.status.value} state, not COMPLETED")

        logger.info("Returning results for completed task: task_id=%s", task_id)
        return {
            "task_id": task_id,
            "result_type": "task_summary",
            "data": db_task.result_summary or {},
            "summary": "Task result data",
        }

    async def execute_task(self, task_id: str) -> None:
        """
        Execute a task using the appropriate runner.
        This function should be called asynchronously.

        Args:
            task_id: ID of the task to execute
        """
        logger.info("Starting execution of task: task_id=%s", task_id)
        db = next(get_db())

        try:
            # Get the task from the database
            db_task: Task = tasks_crud.get_task(db=db, task_id=task_id)
            if not db_task:
                logger.error(f"Task not found: {task_id}")
                return

            # Update task status to VALIDATING
            logger.info("Updating task status to VALIDATING: task_id=%s", task_id)
            db_task: Task = tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.VALIDATING, actor="system")

            try:
                # Validate the task configuration
                logger.info("Validating task configuration: task_id=%s", task_id)
                runner = get_runner_for_task_type(db_task.task_type)
                runner.validate_config(db_task.submitted_configs)
                logger.debug("Task configuration validated successfully: task_id=%s", task_id)

                # Update task status to PREPARING
                logger.info("Updating task status to PREPARING: task_id=%s", task_id)
                db_task: Task = tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.PREPARING, actor="system")

                # Submit the task to the runner
                logger.info("Submitting task to runner: task_id=%s", task_id)
                task_base = await runner.submit_task(runner.from_dao(db_task))
                logger.debug("Task submitted to runner: task_id=%s", task_id)

                # Update task status to RUNNING and include execution details
                execution_details = {"log_file": task_base.log_file}

                logger.info("Updating task status to RUNNING: task_id=%s", task_id)
                db_task = tasks_crud.update_task_status(
                    db=db, task_id=task_id, new_status=TaskStatus.RUNNING, actor="system", execution_details=execution_details
                )

                # Start background monitoring of the task
                logger.info("Starting background monitoring for task: task_id=%s", task_id)
                self._start_task_monitoring(task_id, runner, task_base)

            except Exception as e:
                # If validation or execution fails, mark the task as failed
                logger.error(f"Error during task validation/execution: {str(e)}", exc_info=True)
                error_info = {"error": str(e), "error_type": e.__class__.__name__, "timestamp": datetime.now(UTC).isoformat()}

                logger.info("Updating task status to FAILED: task_id=%s", task_id)
                tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.FAILED, actor="system", error_info=error_info)
                logger.error(f"Failed to execute task {task_id}: {str(e)}", exc_info=True)

        except Exception as e:
            logger.error(f"Error executing task {task_id}: {str(e)}", exc_info=True)

    def _start_task_monitoring(self, task_id: str, runner: TaskRunnerBase, task_base: TaskBase) -> None:
        """
        Start a background task to monitor the task's progress

        Args:
            task_id: ID of the task to monitor
            runner: The task runner instance
            task_base: The task instance
        """
        logger.info("Setting up monitoring for task: task_id=%s", task_id)

        # Create and store the monitoring task
        logger.debug("Creating monitoring task: task_id=%s", task_id)
        monitoring_task = asyncio.create_task(self._monitor_task(task_id, runner, task_base))
        self._monitoring_tasks[task_id] = monitoring_task

        # Set up callback to clean up when monitoring is done
        logger.debug("Setting up cleanup callback for monitoring task: task_id=%s", task_id)
        monitoring_task.add_done_callback(lambda _: self._monitoring_tasks.pop(task_id, None))

        # Start timeout monitor if timeout is set
        if task_base.task_timeout_seconds > 0:
            logger.info("Setting up timeout monitor for task: task_id=%s, timeout=%s seconds", task_id, task_base.task_timeout_seconds)
            timeout_task = asyncio.create_task(self._task_timeout_monitor(task_id, runner, task_base, task_base.task_timeout_seconds))

            # Store the timeout task with a unique key
            self._monitoring_tasks[f"{task_id}_timeout"] = timeout_task

            # Clean up when done
            logger.debug("Setting up cleanup callback for timeout task: task_id=%s", task_id)
            timeout_task.add_done_callback(lambda _: self._monitoring_tasks.pop(f"{task_id}_timeout", None))

    async def _monitor_task(self, task_id: str, runner: TaskRunnerBase, task: TaskBase) -> None:
        """
        Monitor a running task and update its status in the database.

        Args:
            task_id: ID of the task being monitored
            runner: The task runner instance
            task_base: The task instance
        """
        logger.info("Starting task monitor loop: task_id=%s", task_id)
        db = next(get_db())

        try:
            # Poll for status periodically
            while True:
                logger.debug("Polling task status from runner: task_id=%s", task_id)
                # Fetch the latest task status from the runner
                updated_task = await runner.fetch_task_status(task)
                logger.debug("Runner reports task status: task_id=%s, status=%s", task_id, updated_task.status.value)

                # Check if the task has expired
                db_task = tasks_crud.get_task(db=db, task_id=task_id)
                if db_task.expires_at and datetime.now().timestamp() > db_task.expires_at.timestamp():
                    # Task has exceeded its timeout, mark as failed
                    logger.warning("Task has exceeded expiration time: task_id=%s, expires_at=%s", task_id, db_task.expires_at.isoformat())
                    error_info = {"error": "Task exceeded its timeout limit", "error_type": "TaskTimeoutError", "timestamp": datetime.now(UTC).isoformat()}

                    logger.info("Updating expired task status to FAILED: task_id=%s", task_id)
                    tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.FAILED, actor="system", error_info=error_info)

                    # Attempt to cancel the task in the runner
                    try:
                        logger.info("Attempting to cancel expired task in runner: task_id=%s", task_id)
                        await runner.cancel(task_id, force=True)
                    except Exception as e:
                        logger.error(f"Failed to cancel expired task {task_id}: {str(e)}", exc_info=True)

                    break

                # Map status from runner to TaskStatus
                db_status = None
                if updated_task.status == TaskStatus.RUNNING:
                    db_status = TaskStatus.RUNNING
                elif updated_task.status == TaskStatus.COMPLETED:
                    db_status = TaskStatus.COMPLETED
                    logger.info("Task completed successfully: task_id=%s", task_id)
                elif updated_task.status == TaskStatus.FAILED:
                    db_status = TaskStatus.FAILED
                    logger.warning("Task failed: task_id=%s", task_id)
                elif updated_task.status == TaskStatus.CANCELLED:
                    db_status = TaskStatus.CANCELLED
                    logger.info("Task was cancelled: task_id=%s", task_id)
                elif updated_task.status == TaskStatus.CANCELLING:
                    db_status = TaskStatus.CANCELLING

                # If we have a status to update, do it
                if db_status and db_status != db_task.status:
                    logger.info("Updating task status: task_id=%s, old_status=%s, new_status=%s", task_id, db_task.status.value, db_status.value)

                    # Get the result if the task has completed
                    result_summary = None
                    error_info = None

                    if db_status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        if db_status == TaskStatus.COMPLETED:
                            logger.debug("Preparing result summary for completed task: task_id=%s", task_id)
                            result_summary = {"success": True, "result": updated_task.result}
                        else:
                            logger.debug("Preparing error info for failed task: task_id=%s", task_id)
                            error_info = {"error": updated_task.result.get("error", "Task failed"), "timestamp": datetime.now(UTC).isoformat()}

                    # Get logs for the task
                    try:
                        logger.debug("Retrieving log summary for task: task_id=%s", task_id)
                        log_summary = runner.get_log_summary(task)
                        execution_details = {"log_summary": log_summary}
                    except Exception as e:
                        logger.warning("Failed to retrieve log summary: task_id=%s, error=%s", task_id, str(e))
                        execution_details = {}

                    # Update task status in the database
                    logger.debug("Persisting updated task status to database: task_id=%s, status=%s", task_id, db_status.value)
                    tasks_crud.update_task_status(
                        db=db,
                        task_id=task_id,
                        new_status=db_status,
                        actor="system",
                        result_summary=result_summary,
                        error_info=error_info,
                        execution_details=execution_details,
                    )

                    # If the task has reached a terminal state, stop monitoring
                    if db_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                        logger.info("Task reached terminal state, stopping monitor: task_id=%s, status=%s", task_id, db_status.value)
                        break
                else:
                    logger.debug("No status change detected: task_id=%s, status=%s", task_id, db_task.status.value)

                # Sleep before polling again
                logger.debug("Sleeping for %s seconds before next poll: task_id=%s", self.polling_interval, task_id)
                await asyncio.sleep(self.polling_interval)

        except Exception as e:
            logger.error(f"Error monitoring task {task_id}: {str(e)}", exc_info=True)
            # Make sure the task is marked as failed
            try:
                logger.info("Updating task status to FAILED due to monitoring error: task_id=%s", task_id)
                tasks_crud.update_task_status(
                    db=db,
                    task_id=task_id,
                    new_status=TaskStatus.FAILED,
                    actor="system",
                    error_info={"error": f"Monitoring error: {str(e)}", "error_type": e.__class__.__name__, "timestamp": datetime.now(UTC).isoformat()},
                )
            except Exception as inner_e:
                logger.error(f"Failed to update task status: {str(inner_e)}", exc_info=True)

    async def _task_timeout_monitor(self, task_id: str, runner: TaskRunnerBase, task_base: TaskBase, timeout_seconds: int):
        """
        Monitor task timeout and cancel if exceeded.

        Args:
            task_id: ID of the task being monitored
            runner: The task runner instance
            task_base: The task instance
            timeout_seconds: The timeout in seconds
        """
        logger.info("Starting timeout monitor for task: task_id=%s, timeout=%s seconds", task_id, timeout_seconds)

        if timeout_seconds <= 0:
            logger.debug("Timeout monitor disabled (timeout <= 0): task_id=%s", task_id)
            return

        try:
            # Wait for the timeout period
            logger.debug("Waiting for timeout period: task_id=%s, timeout=%s seconds", task_id, timeout_seconds)
            await asyncio.sleep(timeout_seconds)

            # Get the current DB status
            db = next(get_db())
            db_task = tasks_crud.get_task(db=db, task_id=task_id)

            # If the task is still running after the timeout, cancel it
            if db_task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                logger.warning(f"Task {task_id} timed out after {timeout_seconds} seconds")

                # Fetch the latest task status from the runner
                logger.debug("Double-checking task status from runner before timeout: task_id=%s", task_id)
                updated_task = await runner.fetch_task_status(task_base)

                # Only proceed if the task is still running
                if updated_task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                    logger.info("Confirmed task is still running, proceeding with timeout: task_id=%s", task_id)
                    # Update error info
                    error_info = {
                        "error": f"Task timed out after {timeout_seconds} seconds",
                        "error_type": "TaskTimeoutError",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }

                    # Update task status to FAILED due to timeout
                    logger.info("Updating timed-out task status to FAILED: task_id=%s", task_id)
                    tasks_crud.update_task_status(db=db, task_id=task_id, new_status=TaskStatus.FAILED, actor="system", error_info=error_info)

                    # Cancel the task
                    logger.info("Forcing cancellation of timed-out task: task_id=%s", task_id)
                    await runner.cancel(task_id, force=True)
                else:
                    logger.info("Task no longer running (status=%s), skipping timeout handling: task_id=%s", updated_task.status.value, task_id)
            else:
                logger.info("Task already in terminal state (status=%s), ignoring timeout: task_id=%s", db_task.status.value, task_id)
        except Exception as e:
            logger.error(f"Error in timeout monitor for task {task_id}: {str(e)}", exc_info=True)
