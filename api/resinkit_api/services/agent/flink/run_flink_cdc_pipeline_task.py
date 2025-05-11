import asyncio
import uuid
from typing import Optional
from pydantic import ValidationError

from resinkit_api.services.agent.common.flink_models import FlinkCdcConfig
from resinkit_api.services.agent.task_base import TaskBase


class RunFlinkCdcPipelineTask(TaskBase):
    def __init__(self, task_config: dict):
        super().__init__(task_config)
        self.job_id = str(uuid.uuid4())
        self.process: Optional[asyncio.subprocess.Process] = None
        self.log_file = f"/tmp/flink_cdc_{self.job_id}.log"
        self.status = "PENDING"
        self.result = None

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        try:
            FlinkCdcConfig(**task_config)
        except ValidationError as e:
            raise ValueError(f"Invalid config: {e}")
