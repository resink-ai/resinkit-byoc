# Flink CDC Pipeline Runner
import asyncio
import os
import tempfile
import yaml
from typing import Any, Dict, List, Optional
from datetime import UTC, datetime

from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.clients.sql_gateway.flink_sql_gateway_client import FlinkSqlGatewayClient
from resinkit_api.core.config import settings
from resinkit_api.core.logging import get_logger
from resinkit_api.db.models import Task, TaskStatus
from resinkit_api.services.agent.flink.flink_resource_manager import FlinkResourceManager
from resinkit_api.services.agent.flink.flink_cdc_pipeline_task import FlinkCdcPipelineTask
from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase, LogEntry
from resinkit_api.services.agent.data_models import TaskExecutionError
from resinkit_api.services.agent.common.log_file_manager import LogFileManager

logger = get_logger(__name__)


class FlinkCdcPipelineRunner(TaskRunnerBase):
    def __init__(self, job_manager: FlinkJobManager, sql_gateway_client: FlinkSqlGatewayClient, runtime_env: dict | None = None):
        """
        Initialize the Flink CDC Pipeline Runner.

        Args:
            job_manager: Optional FlinkJobManager instance
            sql_gateway_client: Optional FlinkSqlGatewayClient instance
            runtime_env: Optional runtime environment configuration
        """
        super().__init__(runtime_env or {})
        self.flink_home = settings.FLINK_HOME
        self.tasks: Dict[str, FlinkCdcPipelineTask] = {}
        self.job_id_to_task_id: Dict[str, str] = {}
        self.job_manager = job_manager
        self.sql_gateway_client = sql_gateway_client
        self.resource_manager = FlinkResourceManager()
        self._temp_dirs = []  # Track temporary directories for cleanup

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        """Validates the configuration for running a Flink CDC pipeline."""
        try:
            FlinkCdcPipelineTask.validate(task_config)
        except Exception as e:
            raise ValueError(f"Invalid Flink CDC pipeline configuration: {str(e)}")

    def from_dao(self, dao: Task, variables: Dict[str, Any] | None = None) -> FlinkCdcPipelineTask:
        """
        Create a FlinkCdcPipelineRunner instance from a Task DAO.

        Args:
            dao: The Task DAO

        Returns:
            The FlinkCdcPipelineRunner instance
        """
        return FlinkCdcPipelineTask.from_dao(dao, variables)

    async def submit_task(self, task: TaskBase) -> TaskBase:
        """
        Submits a Flink CDC pipeline job.

        Raises:
            TaskExecutionError: If job submission fails
        """
        self.tasks[task.task_id] = task

        # Prepare environment variables and artifacts
        env_vars = await self._prepare_environment(task)

        # Create configuration files
        config_files = await self._prepare_config_files(task)

        # Prepare the command to run
        cmd = await self._build_flink_command(task, config_files)

        lfm = LogFileManager(task.log_file, limit=1000, logger=logger)

        # Execute the command
        logger.info(f"Starting Flink CDC Pipeline: {task.name}")
        task.status = TaskStatus.RUNNING

        try:
            # Run the Flink command
            process = await asyncio.create_subprocess_exec(*cmd, stdout=open(task.log_file, "a"), stderr=open(task.log_file, "a"), env=env_vars)
            task.process = process

            # Update execution_details with command and log file information
            task.execution_details = {"log_file": task.log_file, "command": " ".join(cmd)}

            lfm.info(f"Started Flink CDC pipeline process for task: {task.name}")
            return task
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}

            # Update error_info with exception details
            task.error_info = {"error": str(e), "error_type": e.__class__.__name__, "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")}

            lfm.error(f"Failed to submit Flink CDC pipeline: {str(e)}")
            logger.error(f"Failed to submit Flink CDC pipeline: {str(e)}", exc_info=True)
            raise TaskExecutionError(f"Failed to submit Flink CDC pipeline: {str(e)}")

    def get_status(self, task: TaskBase) -> str:
        """Gets the status of a submitted Flink CDC pipeline job."""
        if not task:
            return "UNKNOWN"
        return task.status.value

    def get_result(self, task: TaskBase) -> Optional[Any]:
        """Gets the result of a completed Flink CDC pipeline job."""
        if not task:
            return None
        return task.result

    def get_log_summary(self, task: TaskBase, level: str = "INFO") -> List[LogEntry]:
        """Gets a summary of logs for a Flink CDC pipeline job."""
        if not task or not task.log_file or not os.path.exists(task.log_file):
            return []

        try:
            log_manager = LogFileManager(task.log_file, limit=1000, logger=logger)
            entries = log_manager.get_entries(level=level)
            return entries[-100:]
        except Exception as e:
            logger.error(f"Failed to read logs for task {task.task_id}: {str(e)}")
            return [LogEntry(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), level="ERROR", message=f"Error reading logs: {str(e)}")]

    async def cancel(self, task: FlinkCdcPipelineTask, force: bool = False) -> FlinkCdcPipelineTask:
        """
        Cancels a running Flink CDC pipeline job.

        Args:
            task: The task instance
            force: Whether to force cancel the job

        Returns:
            The updated task instance

        Raises:
            TaskExecutionError: If cancellation fails
        """
        if not task:
            logger.warning(f"Task {task.task_id} not found")
            return task

        lfm = LogFileManager(task.log_file, limit=1000, logger=logger)

        if task.status not in [TaskStatus.RUNNING, TaskStatus.PENDING]:
            lfm.info(f"Task {task.task_id} is not running, current status: {task.status.value}")
            return task

        task.status = TaskStatus.CANCELLING

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
                    lfm.warning(f"Timeout waiting for task {task.task_id} to terminate, forcing kill")
                    task.process.kill()

            # If the job is running in Flink and we have the job ID, also cancel it there
            flink_job_id = task.result.get("flink_job_id") if task.result else None
            if flink_job_id and self.job_manager:
                # Cancel the job in Flink (this would require additional implementation
                # for the actual Flink job cancellation API call)
                lfm.info(f"Cancelling Flink job {flink_job_id}")
                # TODO: Implement actual Flink job cancellation via API

            task.status = TaskStatus.CANCELLED
            lfm.info(f"Successfully cancelled task {task.task_id}")
            return task
        except Exception as e:
            lfm.error(f"Failed to cancel task {task.task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.result = {"error": f"Cancel failed: {str(e)}"}
            raise TaskExecutionError(f"Failed to cancel task: {str(e)}")

    async def shutdown(self):
        """Shutdown the runner, cancel all tasks and clean up resources."""
        logger.info("Shutting down Flink CDC Pipeline Runner")

        # Cancel all running tasks
        running_tasks = [task_id for task_id, task in self.tasks.items() if task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]]

        for task_id in running_tasks:
            try:
                logger.info(f"Cancelling task {task_id} during shutdown")
                updated_task = await self.cancel(self.tasks[task_id], force=True)
                # Update our local tasks dict with the updated task
                self.tasks[task_id] = updated_task
            except Exception as e:
                logger.error(f"Error cancelling task {task_id} during shutdown: {str(e)}")

        # Clean up resources
        self._cleanup_resources()

    def _cleanup_resources(self):
        """Clean up all temporary resources."""
        # Clean up resource manager
        try:
            self.resource_manager.cleanup()
            logger.info("Resource manager cleanup completed")
        except Exception as e:
            logger.error(f"Error cleaning up resource manager: {str(e)}")

        # Clean up temporary directories
        for temp_dir in self._temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    import shutil

                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.error(f"Failed to clean up temporary directory {temp_dir}: {str(e)}")

    async def _prepare_environment(self, task: FlinkCdcPipelineTask) -> Dict[str, str]:
        """Prepares the environment variables for running a Flink CDC pipeline."""
        env = os.environ.copy()

        # Add FLINK_HOME if not already set
        if "FLINK_HOME" not in env:
            env["FLINK_HOME"] = self.flink_home

        # Add any additional environment variables from the configuration
        if "environment" in task.task_config:
            for key, value in task.task_config.get("environment", {}).items():
                if isinstance(value, str):
                    env[key.upper()] = value

        return env

    async def _prepare_config_files(self, task: FlinkCdcPipelineTask) -> Dict[str, str]:
        """Prepares configuration files needed for the Flink CDC pipeline."""
        config_files = {}

        # Create a temporary directory for configuration files
        temp_dir = tempfile.mkdtemp(prefix="flink_cdc_")
        self._temp_dirs.append(temp_dir)  # Track for cleanup

        # Create pipeline configuration file
        if task.job:
            job_config_path = os.path.join(temp_dir, "job-config.yaml")
            with open(job_config_path, "w") as f:
                yaml.dump(task.job, f, default_flow_style=False, sort_keys=False)
            config_files["job_config"] = job_config_path
        return config_files

    async def _build_flink_command(self, task: FlinkCdcPipelineTask, config_files: Dict[str, str]) -> List[str]:
        """Builds the command to run the Flink CDC pipeline."""
        # Base command using flink-cdc.sh
        cmd = [f"{settings.FLINK_CDC_HOME}/bin/flink-cdc.sh"]

        # Add flink-home parameter
        cmd.extend(["--flink-home", self.flink_home])

        # Process resources using the resource manager
        jar_paths = []
        classpath_jars = []

        if task.resources:
            resource_paths = await self.resource_manager.process_resources(task.resources)
            jar_paths = resource_paths["jar_paths"]
            classpath_jars = resource_paths["classpath_jars"]

        # Add jars to command
        if jar_paths:
            cmd.extend(["--jar", ",".join(jar_paths)])

        # Add classpath jars if any
        if classpath_jars:
            classpath = ":".join(classpath_jars)
            # Add to existing CLASSPATH if it exists
            if "CLASSPATH" in os.environ:
                classpath = f"{os.environ['CLASSPATH']}:{classpath}"
            os.environ["CLASSPATH"] = classpath
            logger.info(f"Added to CLASSPATH: {classpath}")

        # Add savepoint path if specified
        if task.runtime and "savepoint_path" in task.runtime:
            savepoint_path = task.runtime["savepoint_path"]
            if savepoint_path:
                cmd.extend(["--from-savepoint", savepoint_path])

                # Add allow-non-restored-state flag if specified
                if task.runtime.get("allow_non_restored_state", False):
                    cmd.append("--allow-nonRestored-state")

        # Add claim-mode if specified
        if task.runtime and "claim_mode" in task.runtime:
            claim_mode = task.runtime["claim_mode"]
            cmd.extend(["--claim-mode", claim_mode])

        # Add target if specified
        if task.runtime and "target" in task.runtime:
            target = task.runtime["target"]
            cmd.extend(["--target", target])

        # Add use-mini-cluster flag if specified
        if task.runtime and task.runtime.get("use_mini_cluster", False):
            cmd.append("--use-mini-cluster")

        # Add global config if specified
        if task.runtime and "global_config" in task.runtime:
            global_config = task.runtime["global_config"]
            cmd.extend(["--global-config", global_config])

        # Finally, add the pipeline configuration file path
        if "pipeline_config" in config_files:
            cmd.append(config_files["pipeline_config"])

        logger.info(f"[IMPORTANT] Flink command: {cmd}")
        return cmd

    async def fetch_task_status(self, task_id: str) -> FlinkCdcPipelineTask:
        """
        Fetches the latest status of a Flink CDC pipeline task.

        Args:
            task_id: The task ID to check status for

        Returns:
            An updated task instance with the latest status

        Raises:
            TaskExecutionError: If status fetching fails
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return None

        # Check if the task has a process
        if not task.process:
            logger.warning(f"Task {task_id} has no process")
            return task

        # Check if the process is still running
        if task.process.returncode is None:
            # Process is still running
            try:
                # Try to check for a Flink job ID if we don't have one yet
                if not task.result.get("flink_job_id"):
                    flink_job_id = await self._extract_flink_job_id(task.log_file)
                    if flink_job_id:
                        logger.info(f"Found Flink job ID for task {task_id}: {flink_job_id}")
                        task.result["flink_job_id"] = flink_job_id
                        self.job_id_to_task_id[flink_job_id] = task_id

                # If we now have a Flink job ID, check its status in the Flink Job Manager
                if task.result.get("flink_job_id") and self.job_manager:
                    flink_job_id = task.result["flink_job_id"]
                    try:
                        job_details = await self.job_manager.get_job_details(flink_job_id)
                        logger.debug(f"Job {flink_job_id} status: {job_details.get('state')}")

                        # Map Flink job status to our task status
                        flink_status = job_details.get("state", "").upper()

                        if flink_status in ["RUNNING", "CREATED", "RESTARTING"]:
                            task.status = TaskStatus.RUNNING
                        elif flink_status in ["FINISHED", "COMPLETED"]:
                            task.status = TaskStatus.COMPLETED
                            task.result.update(job_details)
                            # Update result_summary with successful results
                            task.result_summary = {"success": True, "job_id": flink_job_id, "details": job_details}
                        elif flink_status in ["FAILED", "FAILING"]:
                            task.status = TaskStatus.FAILED
                            error_message = job_details.get("failure-cause", {}).get("stack-trace", "Unknown error")
                            task.result["error"] = error_message
                            # Update error_info with error details
                            task.error_info = {
                                "error": error_message,
                                "error_type": "FlinkJobError",
                                "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                                "job_id": flink_job_id,
                                "job_details": job_details,
                            }
                        elif flink_status in ["CANCELED", "CANCELLING"]:
                            task.status = TaskStatus.CANCELLED
                    except Exception as e:
                        logger.warning(f"Failed to get job details for {flink_job_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Error updating task {task_id} status: {str(e)}")
                raise TaskExecutionError(f"Failed to update task status: {str(e)}")
        else:
            # Process has exited
            exit_code = task.process.returncode
            logger.info(f"Task {task_id} process exited with code {exit_code}")

            if exit_code == 0:
                task.status = TaskStatus.COMPLETED
                # Update result_summary for successful completion
                task.result_summary = {"success": True, "exit_code": exit_code, "job_id": task.result.get("flink_job_id")}
            else:
                task.status = TaskStatus.FAILED
                error_message = f"Process exited with code {exit_code}"
                task.result["error"] = error_message
                # Update error_info for process failure
                task.error_info = {
                    "error": error_message,
                    "error_type": "ProcessExitError",
                    "exit_code": exit_code,
                    "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
                }

        return task

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
