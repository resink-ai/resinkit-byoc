import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.db.models import Task


class RunFlinkCdcPipelineTask(TaskBase):
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str = "",
        task_timeout_seconds: int = 3600,
        created_at: datetime = None,
        pipeline: Dict[str, Any] = None,
        runtime: Dict[str, Any] = None,
        resources: Dict[str, Any] = None,
    ):
        super().__init__(
            task_type="FLINK_CDC_PIPELINE",
            name=name,
            description=description,
            task_timeout_seconds=task_timeout_seconds,
            task_id=task_id,
            created_at=created_at,
        )
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file = f"/tmp/flink_cdc_{self.task_id}.log"
        self.result = None
        self.execution_details: Dict[str, Any] = {}
        self.pipeline = pipeline or {}
        self.runtime = runtime or {}
        self.resources = resources or {}

    @classmethod
    def from_config(cls, task_config: dict) -> "RunFlinkCdcPipelineTask":
        cls.validate(task_config)
        return cls(
            task_id=task_config.get("task_id"),
            name=task_config.get("name", f"flink_cdc_pipeline_{uuid.uuid4()}"),
            description=task_config.get("description", ""),
            task_timeout_seconds=task_config.get("task_timeout_seconds", 3600),
            created_at=task_config.get("created_at"),
            pipeline=task_config.get("pipeline", {}),
            runtime=task_config.get("runtime", {}),
            resources=task_config.get("resources", {}),
        )

    @classmethod
    def from_dao(cls, task_dao: Task) -> "RunFlinkCdcPipelineTask":
        config = task_dao.submitted_configs or {}
        return cls(
            task_id=task_dao.task_id,
            name=task_dao.task_name,
            description=task_dao.description,
            task_timeout_seconds=task_dao.task_timeout_seconds,
            created_at=task_dao.created_at,
            pipeline=config.get("pipeline", {}),
            runtime=config.get("runtime", {}),
            resources=config.get("resources", {}),
        )

    @classmethod
    def validate(cls, config: dict) -> None:
        """Validate the RunFlinkCdcPipelineTask configuration dictionary."""
        TaskBase.validate(config)
        if not config.get("pipeline"):
            raise ValueError("Missing required 'pipeline' configuration")
        runtime = config.get("runtime")
        if runtime is not None and not isinstance(runtime, dict):
            raise ValueError("Runtime configuration must be a dictionary")
        resources = config.get("resources")
        if resources is not None and not isinstance(resources, dict):
            raise ValueError("Resources configuration must be a dictionary")
