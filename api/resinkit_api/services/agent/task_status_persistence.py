from resinkit_api.db.tasks_crud import update_task_status
from resinkit_api.db.models import TaskStatus
from resinkit_api.db.database import SessionLocal
from datetime import datetime, UTC
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatusPersistenceMixin:
    async def persist_task_status(self, task, status: TaskStatus, error_message: str = None):
        """
        Persist task status to the database.
        Args:
            task: The task instance (must have task_id, result, etc.)
            status: The TaskStatus enum value
            error_message: Optional error message for failed tasks
        """
        try:
            error_info = None
            result_summary = None
            execution_details = None
            if status == TaskStatus.FAILED and error_message:
                error_info = {"error": error_message, "timestamp": datetime.now(UTC).isoformat()}
            if status == TaskStatus.COMPLETED:
                result_summary = {"success": True, "result": getattr(task, "result", None)}
            # Add log summary if available
            log_summary = None
            try:
                if hasattr(self, "get_log_summary"):
                    log_summary = self.get_log_summary(task)
            except Exception:
                pass
            execution_details = {"task_id": task.task_id}
            if log_summary:
                execution_details["log_summary"] = log_summary
            db = SessionLocal()
            try:
                update_task_status(
                    db=db,
                    task_id=task.task_id,
                    new_status=status,
                    actor="system",
                    error_info=error_info,
                    result_summary=result_summary,
                    execution_details=execution_details,
                )
                logger.info(f"Persisted task {task.task_id} status: {status}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to persist task {getattr(task, 'task_id', '?')} status: {str(e)}")
