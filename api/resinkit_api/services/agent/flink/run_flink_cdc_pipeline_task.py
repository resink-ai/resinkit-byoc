import asyncio
import uuid
from typing import Optional, Dict, Any

from resinkit_api.services.agent.task_base import TaskBase


class RunFlinkCdcPipelineTask(TaskBase):
    def __init__(self, task_config: dict):
        super().__init__(task_config)
        self.job_id = str(uuid.uuid4())
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file = f"/tmp/flink_cdc_{self.job_id}.log"
        self.status = "PENDING"
        self.result = None
        self.flink_job_id: Optional[str] = None
        self.execution_details: Dict[str, Any] = {}

    def validate(self) -> None:
        """Validate the task configuration."""
        # Check for required fields
        if not self.task_config.get("pipeline"):
            raise ValueError("Missing required 'pipeline' configuration")
        
        # Validate runtime configuration if present
        runtime = self.task_config.get("runtime", {})
        if runtime and not isinstance(runtime, dict):
            raise ValueError("Runtime configuration must be a dictionary")
            
        # Validate resources if present
        resources = self.task_config.get("resources", {})
        if resources and not isinstance(resources, dict):
            raise ValueError("Resources configuration must be a dictionary")

