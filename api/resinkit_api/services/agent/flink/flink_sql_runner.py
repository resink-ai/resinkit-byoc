import os
from typing import Any, Dict, List, Optional
from datetime import datetime

from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.clients.sql_gateway.flink_session import FlinkSession
from resinkit_api.clients.sql_gateway.flink_sql_gateway_client import FlinkSqlGatewayClient
from resinkit_api.clients.sql_gateway.flink_operation import FlinkOperation, ResultsFetchOpts
from resinkit_api.core.logging import get_logger
from resinkit_api.db.models import Task, TaskStatus
from resinkit_api.services.agent.flink.flink_resource_manager import FlinkResourceManager
from resinkit_api.services.agent.flink.flink_sql_task import FlinkSQLTask
from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase, LogEntry
from resinkit_api.services.agent.data_models import TaskExecutionError
from resinkit_api.services.agent.common.log_file_manager import LogFileManager
import pandas as pd
import json

logger = get_logger(__name__)

DEFAULT_POLLING_OPTIONS = ResultsFetchOpts(
    max_poll_secs=30,
    poll_interval_secs=0.5,
    n_row_limit=100,
)


def _df_to_json(df: pd.DataFrame) -> Dict[str, Any]:
    return json.loads(df.to_json(orient="records", date_format="iso"))


class FlinkSQLRunner(TaskRunnerBase):
    """Runner for executing Flink SQL jobs via the SQL Gateway."""

    def __init__(self, job_manager: FlinkJobManager, sql_gateway_client: FlinkSqlGatewayClient, runtime_env: dict | None = None):
        """
        Initialize the Flink SQL Runner.

        Args:
            job_manager: FlinkJobManager instance for job management
            sql_gateway_client: FlinkSqlGatewayClient instance for SQL Gateway interaction
            runtime_env: Optional runtime environment configuration
        """
        super().__init__(runtime_env or {})
        self.job_manager = job_manager
        self.sql_gateway_client = sql_gateway_client
        self.resource_manager = FlinkResourceManager()
        self.tasks: Dict[str, FlinkSQLTask] = {}
        self.task_id_to_session_id: Dict[str, str] = {}
        self.task_id_to_operation_ids: Dict[str, List[Any]] = {}

    @classmethod
    def validate_config(cls, task_config: dict) -> None:
        """
        Validates the configuration for running a Flink SQL job.

        Args:
            task_config: The task configuration dictionary

        Raises:
            ValueError: If the configuration is invalid
        """
        try:
            FlinkSQLTask.validate(task_config)
        except Exception as e:
            raise ValueError(f"Invalid Flink SQL configuration: {str(e)}")

    def from_dao(self, dao: Task, variables: Dict[str, Any] | None = None) -> FlinkSQLTask:
        """
        Create a FlinkSQLRunner instance from a Task DAO.

        Args:
            dao: The Task DAO

        Returns:
            The FlinkSQLRunner instance
        """
        return FlinkSQLTask.from_dao(dao, variables)

    async def submit_task(self, task: FlinkSQLTask) -> FlinkSQLTask:
        """
        Submits a Flink SQL job to the SQL Gateway.

        Args:
            task: The task instance

        Returns:
            The created task instance

        Raises:
            TaskExecutionError: If job submission fails
        """
        task_id = task.task_id
        self.tasks[task_id] = task

        # Process resources
        resources = await self.resource_manager.process_resources(task.resources)

        lfm = LogFileManager(task.log_file, limit=1000, logger=logger)

        try:
            # Update task status
            task.status = TaskStatus.RUNNING
            if task.result_summary.get("results") is None:
                task.result_summary["results"] = []
            if task.result_summary.get("job_ids") is None:
                task.result_summary["job_ids"] = []
            if task.result_summary.get("is_query") is None:
                task.result_summary["is_query"] = []
            lfm.info(f"Starting Flink SQL job: {task.name}")

            # Create session properties
            session_properties = self._create_session_properties(task, resources)
            session_name = f"session_{task_id}"

            # Create and open a session; no need to close it, going to reuse it
            session = self.sql_gateway_client.get_session(
                properties=session_properties,
                session_name=session_name,
                create_if_not_exist=True,
            )
            lfm.info(f"Created Flink SQL session: {session_name}")
            # Execute each SQL statement
            operation_handles = []
            for i, sql in enumerate(task.sql_statements):
                lfm.info(f"Executing SQL statement {i+1}/{len(task.sql_statements)}")
                lfm.info(f"SQL: {sql}")

                # Execute the statement
                async with session.execute(sql).asyncio() as operation:
                    # Store the operation handle for later status checks
                    operation_handles.append(operation.operation_handle)
                    result_df, res_data = await operation.fetch(
                        polling_opts=ResultsFetchOpts(
                            max_poll_secs=task.connection_timeout_seconds,
                            poll_interval_secs=0.5,
                            n_row_limit=100,
                        )
                    ).asyncio()
                    lfm.info(f"Results: {result_df.to_string()}")
                    task.result_summary["results"].append(_df_to_json(result_df))
                    task.result_summary["job_ids"].append(res_data.job_id)
                    task.result_summary["is_query"].append(res_data.is_query_result)

                    # Get the operation status
                    status = await operation.status().asyncio()
                    lfm.info(f"Operation status: {status.status}")
                    # if this is the last and the status is "FINISHED"
                    if i == len(task.sql_statements) - 1 and status.status == "FINISHED":
                        task.status = TaskStatus.COMPLETED
                        lfm.info(f"Flink SQL job completed successfully, name: {task.name}, id: {task.task_id}")
                    else:
                        lfm.info(f"Flink SQL job submitted successfully, name: {task.name}, id: {task.task_id}, status: {status.status}")

            # Store the operation handles
            task.operation_handles = operation_handles
            task.result["operation_handles"] = operation_handles
            task.result["session_name"] = session_name
            task.result["session_id"] = session.session_handle

            # Update execution_details with important execution information
            task.execution_details = {"log_file": task.log_file, "session_name": session_name, "session_id": session.session_handle}

            # Store the session name
            self.task_id_to_session_id[task_id] = session.session_handle
            self.task_id_to_operation_ids[task_id] = operation_handles
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}
            # Store error information in error_info
            task.error_info = {"error": str(e), "error_type": e.__class__.__name__, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            lfm.error(f"Failed to submit Flink SQL job: {str(e)}")
            logger.error(f"Failed to submit Flink SQL job: {str(e)}", exc_info=True)
            # No need to raise an exception here, task reaches end state, TaskManager will catch this and update the task status
        return task

    def get_status(self, task: TaskBase) -> str:
        """
        Gets the status of a submitted Flink SQL job.

        Args:
            task: The task instance

        Returns:
            The task status
        """
        if not task:
            return "UNKNOWN"
        return task.status.value

    def get_result(self, task: FlinkSQLTask) -> Optional[Any]:
        """
        Gets the result of a completed Flink SQL job.

        Args:
            task: The task instance

        Returns:
            The task result
        """
        if not task:
            return None
        return task.result

    def get_log_summary(self, task: FlinkSQLTask, level: str = "INFO") -> List[LogEntry]:
        """
        Gets a summary of logs for a Flink SQL job.

        Args:
            task: The task instance
            level: The log level to filter by

        Returns:
            A list of log entries
        """
        if not task or not task.log_file or not os.path.exists(task.log_file):
            return []

        try:
            lfm = LogFileManager(task.log_file, limit=1000, logger=logger)
            entries = lfm.get_entries(level=level)
            return entries
        except Exception as e:
            logger.error(f"Failed to read logs for task {task.task_id}: {str(e)}")
            return [LogEntry(timestamp=datetime.now().timestamp(), level="ERROR", message=f"Error reading logs: {str(e)}")]

    async def cancel(self, task: FlinkSQLTask, force: bool = False) -> FlinkSQLTask:
        """
        Cancels a running Flink SQL job.

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
            # Get session name
            session_name = task.result.get("session_name")
            if not session_name:
                lfm.warning(f"No session name found for task {task.task_id}")
                return task

            # Get session
            with self.sql_gateway_client.get_session(session_name=session_name, create_if_not_exist=False) as session:
                if not session.was_alive:
                    lfm.warning(f"Session {session_name} was not alive when cancelling task {task.task_id}, consider task completed")
                    task.status = TaskStatus.COMPLETED
                    return task

                # Cancel each operation
                for op_handle in task.operation_handles:
                    try:
                        async with FlinkOperation(session, op_handle) as operation:
                            response = await operation.cancel().asyncio()
                            lfm.info(f"Cancelled operation {op_handle} for task {task.task_id}, response: {response}")
                    except Exception as e:
                        lfm.error(f"Failed to cancel operation {op_handle}: {str(e)}")
                task.status = TaskStatus.CANCELLED
                lfm.info(f"Successfully cancelled task {task.task_id}")
                return task
        except Exception as e:
            lfm.error(f"Failed to cancel task {task.task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.result["error"] = f"Cancel failed: {str(e)}"
            raise TaskExecutionError(f"Failed to cancel task: {str(e)}")

    async def shutdown(self):
        """Shutdown the runner, cancel all tasks and clean up resources."""
        logger.info("Shutting down Flink SQL Runner")

        # Cancel all running tasks
        running_tasks = [task_id for task_id, task in self.tasks.items() if task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]]

        for task_id in running_tasks:
            lfm = LogFileManager(self.tasks[task_id].log_file, limit=1000, logger=logger)
            try:
                logger.info(f"Cancelling task {task_id} during shutdown")
                updated_task = await self.cancel(self.tasks[task_id], force=True)
                # Update our local tasks dict with the updated task
                self.tasks[task_id] = updated_task
            except Exception as e:
                lfm.error(f"Error cancelling task {task_id} during shutdown: {str(e)}")
        # Clean up resources
        try:
            self.resource_manager.cleanup()
            logger.info("Resource manager cleanup completed")
        except Exception as e:
            logger.error(f"Error cleaning up resources: {str(e)}")

    def _create_session_properties(self, task: FlinkSQLTask, resources: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Create session properties for the Flink SQL Gateway.

        Args:
            task: The task instance
            resources: Processed resources

        Returns:
            Dictionary of session properties
        """
        properties = {}

        # Add jar paths
        if resources.get("jar_paths"):
            jar_paths = ";".join(resources["jar_paths"])
            properties["pipeline.jars"] = jar_paths

        # Add classpath jars
        if resources.get("classpath_jars"):
            classpath_jars = ";".join(resources["classpath_jars"])
            properties["pipeline.classpaths"] = classpath_jars

        # Set parallelism
        properties["parallelism.default"] = str(task.parallelism)

        # Add execution mode (we're using streaming for SQL Gateway)
        properties["execution.runtime-mode"] = "streaming"

        # Set pipeline name
        properties["pipeline.name"] = task.pipeline_name

        return properties

    async def fetch_task_status(self, task: FlinkSQLTask) -> FlinkSQLTask:
        """
        Fetches the latest status of a Flink SQL task.

        Args:
            task: The task instance

        Returns:
            An updated task instance with the latest status

        Raises:
            TaskExecutionError: If fetching status fails
        """
        if not task:
            logger.warning(f"Task {task.task_id} not found")
            return None

        task_id = task.task_id
        session_id = self.task_id_to_session_id[task_id]
        operation_id = self.task_id_to_operation_ids[task_id][-1]

        lfm = LogFileManager(task.log_file, limit=1000, logger=logger)

        # Initialize status as the current task status
        new_status = task.status
        error_message = None
        if session_id and operation_id:
            try:
                session_status = FlinkSession.get_operation_status(self.sql_gateway_client.get_client(), session_id, operation_id)
                if session_status:
                    new_status = session_status
            except Exception as e:
                lfm.error(f"Error fetching status for task {task.task_id}: {str(e)}")
                new_status = TaskStatus.FAILED
                error_message = "Failed to fetch status for task, task failed too fast, likely invalid SQL"
        else:
            # Mark as failed if no session or operation ID found
            lfm.warning(f"No session or operation ID found for task {task.task_id}")
            new_status = TaskStatus.FAILED
            error_message = "No session or operation ID found"

        # Update task status if changed
        if new_status != task.status:
            task.status = new_status
            if new_status == TaskStatus.FAILED and error_message:
                task.result_summary = task.result_summary or {}
                task.result_summary["error"] = error_message
                # Update error_info with the error message
                task.error_info = {"error": error_message, "error_type": "TaskStatusError", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            elif new_status == TaskStatus.COMPLETED:
                # Update result_summary with successful results
                task.result_summary = {"success": True, "results": task.result.get("results", []), "job_id": task.result.get("job_id")}

        return task
