import asyncio
import uuid
import os
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

    def update_status(self, status: str, message: Optional[str] = None) -> None:
        """Update the status of the task."""
        self.status = status
        if message and not self.result:
            self.result = {}
        if message and self.result:
            self.result["message"] = message

    def update_execution_details(self, details: Dict[str, Any]) -> None:
        """Update execution details of the task."""
        self.execution_details.update(details)

    def get_task_summary(self) -> Dict[str, Any]:
        """Get a summary of the task."""
        return {
            "job_id": self.job_id,
            "task_type": self.task_type,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "flink_job_id": self.flink_job_id,
            "log_file": self.log_file if os.path.exists(self.log_file) else None,
            "result": self.result,
        }

    def get_command_summary(self) -> Optional[str]:
        """Get the executed command summary."""
        if "command" in self.execution_details:
            return self.execution_details["command"]
        return None
