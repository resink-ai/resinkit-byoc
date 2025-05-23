import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.db.models import Task


class FlinkCdcPipelineTask(TaskBase):
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str = "",
        connection_timeout_seconds: int = 30,
        task_timeout_seconds: int = 3600,
        created_at: datetime = None,
        job: Dict[str, Any] = None,
        runtime: Dict[str, Any] = None,
        resources: Dict[str, Any] = None,
        error_info: Dict[str, Any] = None,
        result_summary: Dict[str, Any] = None,
        execution_details: Dict[str, Any] = None,
        progress_details: Dict[str, Any] = None,
    ):
        super().__init__(
            task_type="FLINK_CDC_PIPELINE",
            name=name,
            description=description,
            connection_timeout_seconds=connection_timeout_seconds,
            task_timeout_seconds=task_timeout_seconds,
            task_id=task_id,
            created_at=created_at,
            error_info=error_info,
            result_summary=result_summary,
            execution_details=execution_details,
            progress_details=progress_details,
        )
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file = f"/tmp/flink_cdc_{self.task_id}.log"
        self.result = {}
        self.job = job or {}
        self.runtime = runtime or {}
        self.resources = resources or {}

    @classmethod
    def from_dao(cls, task_dao: Task, variables: Dict[str, Any] | None = None) -> "FlinkCdcPipelineTask":
        # Get submitted configs and apply variable substitution if needed
        config = task_dao.submitted_configs or {}
        if variables and config:
            config = TaskBase.render_with_variables(config, variables)

        connection_timeout_seconds = config.get("connection_timeout_seconds", 30)
        return cls(
            task_id=task_dao.task_id,
            name=task_dao.task_name,
            description=task_dao.description,
            connection_timeout_seconds=connection_timeout_seconds,
            task_timeout_seconds=task_dao.task_timeout_seconds,
            created_at=task_dao.created_at,
            job=config.get("job", {}),
            runtime=config.get("runtime", {}),
            resources=config.get("resources", {}),
            error_info=task_dao.error_info,
            result_summary=task_dao.result_summary,
            execution_details=task_dao.execution_details,
            progress_details=task_dao.progress_details,
        )

    @classmethod
    def validate(cls, config: dict) -> None:
        """Validate the FlinkCdcPipelineTask configuration dictionary."""
        TaskBase.validate(config)
        if not config.get("job"):
            raise ValueError("Missing required 'job' configuration")
        runtime = config.get("runtime")
        if runtime is not None and not isinstance(runtime, dict):
            raise ValueError("Runtime configuration must be a dictionary")
        resources = config.get("resources")
        if resources is not None and not isinstance(resources, dict):
            raise ValueError("Resources configuration must be a dictionary")
