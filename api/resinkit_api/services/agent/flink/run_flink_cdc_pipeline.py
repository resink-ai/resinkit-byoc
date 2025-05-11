import asyncio
import uuid
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError, model_validator

from resinkit_api.services.agent.common.flink_models import FlinkCdcConfig
from resinkit_api.services.agent.common.task_base import PipelineTaskBase


class RunFlinkCdcPipelineTask(PipelineTaskBase):
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

    async def submit_job(self) -> str:
        # Write config to YAML file
        config_path = f"/tmp/{self.job_id}.yaml"
        with open(config_path, "w") as f:
            import yaml
            yaml.dump(self.task_config, f)
        # Start the Flink CDC job
        self.process = await asyncio.create_subprocess_exec(
            "bash", "bin/flink-cdc.sh", config_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        self.status = "RUNNING"
        asyncio.create_task(self._capture_logs())
        return self.job_id

    async def _capture_logs(self):
        assert self.process
        with open(self.log_file, "wb") as f:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break
                f.write(line)
        await self.process.wait()
        self.status = "FINISHED" if self.process.returncode == 0 else "FAILED"

    def get_status(self) -> str:
        return self.status

    def get_result(self) -> Optional[Any]:
        return self.result

    def get_log_summary(self, level: str = "INFO") -> str:
        if not os.path.exists(self.log_file):
            return ""
        with open(self.log_file, "r") as f:
            lines = [line for line in f if level in line]
        return "\n".join(lines[-20:])  # last 20 lines

    async def cancel(self, force: bool = False):
        if self.process and self.process.returncode is None:
            if force:
                self.process.kill()
            else:
                self.process.terminate()
            await self.process.wait()
            self.status = "CANCELLED"
