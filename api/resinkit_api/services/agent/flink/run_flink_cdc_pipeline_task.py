import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.db.models import Task


class RunFlinkCdcPipelineTask(TaskBase):
    def __init__(self, task_type: str = "FLINK_CDC_PIPELINE", name: str = '', 
                 description: str = '', task_timeout_seconds: int = 3600, 
                 created_at: datetime = datetime.now(), 
                 pipeline: dict = None, runtime: dict = None, resources: dict = None):
        super().__init__(task_type, name, description, task_timeout_seconds, created_at)
        self.job_id = str(uuid.uuid4())
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file = f"/tmp/flink_cdc_{self.job_id}.log"
        self.status = "PENDING"
        self.result = None
        self.flink_job_id: Optional[str] = None
        self.execution_details: Dict[str, Any] = {}
        
        # Pipeline-specific configurations
        self.pipeline = pipeline or {}
        self.runtime = runtime or {}
        self.resources = resources or {}

    @classmethod
    def from_config(cls, task_config: dict) -> 'RunFlinkCdcPipelineTask':
        return cls(
            task_type="FLINK_CDC_PIPELINE",
            name=task_config.get("name", f"flink_cdc_pipeline_{uuid.uuid4()}"),
            description=task_config.get("description", ""),
            task_timeout_seconds=task_config.get("task_timeout_seconds", 3600),
            pipeline=task_config.get("pipeline", {}),
            runtime=task_config.get("runtime", {}),
            resources=task_config.get("resources", {})
        )
    
    @classmethod
    def from_dao(cls, task_dao: Task) -> 'RunFlinkCdcPipelineTask':
        config = task_dao.config or {}
        return cls(
            task_type=task_dao.task_type,
            name=task_dao.name,
            description=task_dao.description,
            task_timeout_seconds=task_dao.task_timeout_seconds,
            created_at=task_dao.created_at,
            pipeline=config.get("pipeline", {}),
            runtime=config.get("runtime", {}),
            resources=config.get("resources", {})
        )

    def validate(self) -> None:
        """Validate the task configuration."""
        # Check for required fields
        if not self.pipeline:
            raise ValueError("Missing required 'pipeline' configuration")
        
        # Validate runtime configuration if present
        if self.runtime and not isinstance(self.runtime, dict):
            raise ValueError("Runtime configuration must be a dictionary")
            
        # Validate resources if present
        if self.resources and not isinstance(self.resources, dict):
            raise ValueError("Resources configuration must be a dictionary")

