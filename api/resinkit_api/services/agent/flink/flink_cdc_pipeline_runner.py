# Flink CDC Pipeline Runner
import asyncio
import json
import os
import tempfile
import uuid
from typing import Any, Dict, List, Optional

from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.core.config import settings
from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.common.flink_models import FlinkCdcConfig
from resinkit_api.services.agent.flink.run_flink_cdc_pipeline_task import RunFlinkCdcPipelineTask
from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase

logger = get_logger(__name__)


class FlinkCdcPipelineRunner(TaskRunnerBase):
    def __init__(self, runtime_env: dict):
        super().__init__(runtime_env)
        self.flink_home = settings.FLINK_HOME
        self.tasks: Dict[str, RunFlinkCdcPipelineTask] = {}
        self.job_id_to_task_id: Dict[str, str] = {}
        try:
            self.job_manager = FlinkJobManager(
                host=self.runtime_env.get("flink_job_manager_host", "localhost"),
                port=self.runtime_env.get("flink_job_manager_port", 8081)
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Flink Job Manager: {str(e)}")
            self.job_manager = None

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        """Validates the configuration for running a Flink CDC pipeline."""
        try:
            FlinkCdcConfig(**task_config)
        except Exception as e:
            raise ValueError(f"Invalid Flink CDC pipeline configuration: {str(e)}")

    async def submit_job(self, task_config: dict) -> TaskBase:
        """Submits a Flink CDC pipeline job."""
        # Validate configuration
        self.validate_config(task_config)
        
        # Create task instance
        task = RunFlinkCdcPipelineTask(task_config)
        self.tasks[task.job_id] = task
        
        # Prepare environment variables and artifacts
        env_vars = await self._prepare_environment(task_config)
        
        # Create configuration files
        config_files = await self._prepare_config_files(task_config)
        
        # Prepare the command to run
        cmd = await self._build_flink_command(task_config, config_files)
        
        # Open log file for the task
        log_file = open(task.log_file, "w")
        
        # Execute the command
        logger.info(f"Starting Flink CDC Pipeline: {task.name}")
        task.status = "RUNNING"
        
        try:
            # Run the Flink command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=log_file,
                stderr=log_file,
                env=env_vars
            )
            task.process = process
            
            # Store the process and update task status
            await self._monitor_job(task)
            
            return task
        except Exception as e:
            task.status = "FAILED"
            task.result = {"error": str(e)}
            logger.error(f"Failed to submit Flink CDC pipeline: {str(e)}")
            raise
        finally:
            log_file.close()

    def get_status(self, task_id: str) -> str:
        """Gets the status of a submitted Flink CDC pipeline job."""
        task = self.tasks.get(task_id)
        if not task:
            return "UNKNOWN"
        return task.status

    def get_result(self, task_id: str) -> Optional[Any]:
        """Gets the result of a completed Flink CDC pipeline job."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        return task.result

    def get_log_summary(self, task_id: str, level: str = "INFO") -> str:
        """Gets a summary of logs for a Flink CDC pipeline job."""
        task = self.tasks.get(task_id)
        if not task or not task.log_file or not os.path.exists(task.log_file):
            return "No logs available"
        
        try:
            # Read the log file and extract relevant lines based on level
            with open(task.log_file, "r") as f:
                logs = f.readlines()
            
            # Filter logs by level
            filtered_logs = [log for log in logs if level in log]
            
            # Return the most recent logs, limited to 100 lines
            return "".join(filtered_logs[-100:])
        except Exception as e:
            logger.error(f"Failed to read logs for task {task_id}: {str(e)}")
            return f"Error reading logs: {str(e)}"

    async def cancel(self, task_id: str, force: bool = False):
        """Cancels a running Flink CDC pipeline job."""
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return
        
        if task.status not in ["RUNNING", "PENDING"]:
            logger.info(f"Task {task_id} is not running, current status: {task.status}")
            return
        
        task.status = "CANCELLING"
        
        try:
            # If we have a process, terminate it
            if task.process:
                if force:
                    task.process.kill()
                else:
                    task.process.terminate()
                
                # Wait for the process to terminate
                try:
                    await asyncio.wait_for(task.process.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for task {task_id} to terminate, forcing kill")
                    task.process.kill()
            
            # If the job is running in Flink and we have the job ID, also cancel it there
            flink_job_id = task.result.get("flink_job_id") if task.result else None
            if flink_job_id and self.job_manager:
                # Cancel the job in Flink (this would require additional implementation
                # for the actual Flink job cancellation API call)
                logger.info(f"Cancelling Flink job {flink_job_id}")
                # TODO: Implement actual Flink job cancellation via API
            
            task.status = "CANCELLED"
            logger.info(f"Successfully cancelled task {task_id}")
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            task.status = "FAILED"
            task.result = {"error": f"Cancel failed: {str(e)}"}
            raise

    async def _prepare_environment(self, task_config: dict) -> Dict[str, str]:
        """Prepares the environment variables for running a Flink CDC pipeline."""
        env = os.environ.copy()
        
        # Add FLINK_HOME if not already set
        if "FLINK_HOME" not in env:
            env["FLINK_HOME"] = self.flink_home
        
        # Add any additional environment variables from the configuration
        if "environment" in task_config:
            for key, value in task_config["environment"].items():
                if isinstance(value, str):
                    env[key.upper()] = value
        
        return env

    async def _prepare_config_files(self, task_config: dict) -> Dict[str, str]:
        """Prepares configuration files needed for the Flink CDC pipeline."""
        config_files = {}
        
        # Create a temporary directory for configuration files
        temp_dir = tempfile.mkdtemp(prefix="flink_cdc_")
        
        # Create pipeline configuration file
        if "pipeline" in task_config:
            pipeline_config_path = os.path.join(temp_dir, "pipeline-config.yaml")
            with open(pipeline_config_path, "w") as f:
                json.dump(task_config["pipeline"], f, indent=2)
            config_files["pipeline_config"] = pipeline_config_path
        
        # Create resources configuration file if needed
        if "resources" in task_config:
            resources_config_path = os.path.join(temp_dir, "resources-config.yaml")
            with open(resources_config_path, "w") as f:
                json.dump(task_config["resources"], f, indent=2)
            config_files["resources_config"] = resources_config_path
        
        return config_files

    async def _build_flink_command(self, task_config: dict, config_files: Dict[str, str]) -> List[str]:
        """Builds the command to run the Flink CDC pipeline."""
        # Base command
        cmd = [f"{self.flink_home}/bin/flink", "run"]
        
        # Add parallelism if specified
        if "environment" in task_config and "parallelism" in task_config["environment"]:
            cmd.extend(["-p", str(task_config["environment"]["parallelism"])])
        
        # Add job name
        job_name = task_config.get("name", f"flink-cdc-{uuid.uuid4()}")
        cmd.extend(["-n", f"\"{job_name}\""])
        
        # Add checkpoint interval if specified
        if "environment" in task_config and "checkpoint_interval" in task_config["environment"]:
            checkpoint_interval = task_config["environment"]["checkpoint_interval"]
            if isinstance(checkpoint_interval, str) and checkpoint_interval.endswith("s"):
                # Convert from "60s" format to milliseconds
                checkpoint_interval = int(checkpoint_interval[:-1]) * 1000
            cmd.extend(["-c", f"execution.checkpointing.interval={checkpoint_interval}"])
        
        # Add savepoint path if specified
        if "runtime" in task_config and "savepoint_path" in task_config["runtime"]:
            savepoint_path = task_config["runtime"]["savepoint_path"]
            if savepoint_path:
                cmd.extend(["-s", savepoint_path])
                
                # Add allow-non-restored-state flag if specified
                if task_config["runtime"].get("allow_non_restored_state", False):
                    cmd.append("--allowNonRestoredState")
        
        # Add jar files
        jars = []
        classpath_entries = []
        
        # Process resources
        if "resources" in task_config:
            resources = task_config["resources"]
            
            # Process Flink CDC jars
            if "flink_cdc_jars" in resources:
                for jar in resources["flink_cdc_jars"]:
                    if jar.get("type") == "lib":
                        jars.append(jar["location"])
                    elif jar.get("type") == "classpath":
                        classpath_entries.append(jar["location"])
            
            # Process regular Flink jars
            if "flink_jars" in resources:
                for jar in resources["flink_jars"]:
                    if "download_link" in jar:
                        jars.append(jar["download_link"])
        
        # Add jars to command
        if jars:
            cmd.extend(["-j", ",".join(jars)])
        
        # Add classpath entries
        if classpath_entries:
            cmd.extend(["-C", ",".join(classpath_entries)])
        
        # Add the main CDC pipeline JAR (assuming it's available in the Flink lib directory)
        cmd.append(f"{self.flink_home}/lib/flink-cdc-pipeline.jar")
        
        # Add the pipeline configuration file
        if "pipeline_config" in config_files:
            cmd.extend(["--pipeline", config_files["pipeline_config"]])
        
        return cmd

    async def _monitor_job(self, task: RunFlinkCdcPipelineTask):
        """
        Starts monitoring the running job in a background task.
        Updates the task status and result based on the job execution.
        """
        # Create a background task to monitor the job
        asyncio.create_task(self._job_monitor_task(task))

    async def _job_monitor_task(self, task: RunFlinkCdcPipelineTask):
        """Background task to monitor a running Flink job."""
        try:
            # Wait for the process to complete
            return_code = await task.process.wait()
            
            # Process the output to find the Flink job ID
            flink_job_id = await self._extract_flink_job_id(task.log_file)
            
            if return_code == 0:
                task.status = "COMPLETED"
                task.result = {
                    "success": True,
                    "flink_job_id": flink_job_id,
                    "message": "CDC pipeline successfully deployed"
                }
                logger.info(f"Flink CDC pipeline {task.job_id} completed successfully")
            else:
                task.status = "FAILED"
                task.result = {
                    "success": False,
                    "flink_job_id": flink_job_id,
                    "return_code": return_code,
                    "message": f"CDC pipeline failed with return code {return_code}"
                }
                logger.error(f"Flink CDC pipeline {task.job_id} failed with return code {return_code}")
        except Exception as e:
            task.status = "FAILED"
            task.result = {
                "success": False,
                "error": str(e),
                "message": f"Exception during job monitoring: {str(e)}"
            }
            logger.error(f"Exception monitoring Flink CDC pipeline {task.job_id}: {str(e)}")

    async def _extract_flink_job_id(self, log_file_path: str) -> Optional[str]:
        """
        Extracts the Flink job ID from the log file.
        Returns None if no job ID could be found.
        """
        if not os.path.exists(log_file_path):
            return None
        
        try:
            with open(log_file_path, "r") as f:
                log_content = f.read()
            
            # Look for job ID pattern in logs - this pattern may need adjustment
            # based on actual Flink output format
            import re
            job_id_match = re.search(r"Job has been submitted with JobID ([a-f0-9]+)", log_content)
            
            if job_id_match:
                return job_id_match.group(1)
            
            return None
        except Exception as e:
            logger.error(f"Failed to extract Flink job ID from log file: {str(e)}")
            return None
