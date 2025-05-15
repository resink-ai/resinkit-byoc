import asyncio
import os
import uuid
from typing import Any, Dict, List, Optional

from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.clients.sql_gateway.flink_sql_gateway_client import FlinkSqlGatewayClient
from resinkit_api.clients.sql_gateway.flink_operation import FlinkOperation
from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.flink.flink_resource_manager import FlinkResourceManager
from resinkit_api.services.agent.flink.flink_sql_task import FlinkSQLTask
from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase

logger = get_logger(__name__)


class FlinkSQLRunner(TaskRunnerBase):
    """Runner for executing Flink SQL jobs via the SQL Gateway."""
    
    def __init__(self, 
                job_manager: FlinkJobManager, 
                sql_gateway_client: FlinkSqlGatewayClient,
                runtime_env: dict | None = None):
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
        self.job_id_to_task_id: Dict[str, str] = {}
        self.session_to_task_id: Dict[str, str] = {}
        
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
            task = FlinkSQLTask.from_config(task_config)
            task.validate()
        except Exception as e:
            raise ValueError(f"Invalid Flink SQL configuration: {str(e)}")

    async def submit_job(self, task_config: dict) -> TaskBase:
        """
        Submits a Flink SQL job to the SQL Gateway.
        
        Args:
            task_config: The task configuration dictionary
            
        Returns:
            The created task instance
            
        Raises:
            Exception: If job submission fails
        """
        # Validate configuration
        self.validate_config(task_config)
        
        # Create task instance
        task = FlinkSQLTask.from_config(task_config)
        task_id = task.job_id
        self.tasks[task_id] = task
        
        # Process resources
        resources = await self.resource_manager.process_resources(task.resources)
        
        # Open log file for the task
        log_file = open(task.log_file, "w")
        
        try:
            # Update task status
            task.status = "RUNNING"
            log_file.write(f"Starting Flink SQL job: {task.name}\n")
            
            # Create session properties
            session_properties = self._create_session_properties(task, resources)
            session_name = f"session_{task_id}"
            
            # Create and open a session
            session = self.sql_gateway_client.get_session(
                properties=session_properties, 
                session_name=session_name
            )
            
            # Start the monitoring task
            asyncio.create_task(self._monitor_task(task, session_name))
            
            log_file.write(f"Created Flink SQL session: {session_name}\n")
            
            # Execute each SQL statement
            operation_handles = []
            for i, sql in enumerate(task.sql_statements):
                log_file.write(f"Executing SQL statement {i+1}/{len(task.sql_statements)}\n")
                log_file.write(f"SQL: {sql}\n")
                
                # Execute the statement
                with session.execute(sql).sync() as operation:
                    # Store the operation handle for later status checks
                    operation_handles.append(operation.operation_handle)
                    
                    # For SELECT statements, fetch and display results
                    if sql.strip().upper().startswith("SELECT"):
                        result_df = operation.fetch().sync()
                        log_file.write(f"Results: {result_df.to_string()}\n")
                    
                    # Get the operation status
                    status = operation.status().sync()
                    log_file.write(f"Operation status: {status.status}\n")
                    
                    # If this is a job submission, extract the job ID
                    if "jobId" in status.info:
                        flink_job_id = status.info["jobId"]
                        log_file.write(f"Flink job ID: {flink_job_id}\n")
                        task.result["flink_job_id"] = flink_job_id
                        self.job_id_to_task_id[flink_job_id] = task_id
                    
            # Store the operation handles
            task.operation_handles = operation_handles
            task.result["operation_handles"] = operation_handles
            task.result["session_name"] = session_name
            
            # Store the session name
            self.session_to_task_id[session_name] = task_id
            
            log_file.write(f"Flink SQL job submitted successfully, name: {task.name}, id: {task.job_id}")
            
            return task
        except Exception as e:
            task.status = "FAILED"
            task.result = {"error": str(e)}
            log_file.write(f"Failed to submit Flink SQL job: {str(e)}\n")
            logger.error(f"Failed to submit Flink SQL job: {str(e)}", exc_info=True)
            raise
        finally:
            log_file.close()

    def get_status(self, task_id: str) -> str:
        """
        Gets the status of a submitted Flink SQL job.
        
        Args:
            task_id: The task ID
            
        Returns:
            The task status
        """
        task = self.tasks.get(task_id)
        if not task:
            return "UNKNOWN"
        return task.status

    def get_result(self, task_id: str) -> Optional[Any]:
        """
        Gets the result of a completed Flink SQL job.
        
        Args:
            task_id: The task ID
            
        Returns:
            The task result
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        return task.result

    def get_log_summary(self, task_id: str, level: str = "INFO") -> str:
        """
        Gets a summary of logs for a Flink SQL job.
        
        Args:
            task_id: The task ID
            level: The log level to filter by
            
        Returns:
            A summary of logs
        """
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
        """
        Cancels a running Flink SQL job.
        
        Args:
            task_id: The task ID
            force: Whether to force cancel the job
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found")
            return
        
        if task.status not in ["RUNNING", "PENDING"]:
            logger.info(f"Task {task_id} is not running, current status: {task.status}")
            return
        
        task.status = "CANCELLING"
        
        try:
            # Get session name
            session_name = task.result.get("session_name")
            if not session_name:
                logger.warning(f"No session name found for task {task_id}")
                return
            
            # Get session
            session = self.sql_gateway_client.get_session(session_name=session_name)
            
            # Cancel each operation
            for op_handle in task.operation_handles:
                try:
                    # Create a FlinkOperation with the handle and cancel it
                    operation = FlinkOperation(session, op_handle)
                    operation.cancel().sync()
                    logger.info(f"Cancelled operation {op_handle} for task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to cancel operation {op_handle}: {str(e)}")
            
            # Close the session if using context manager
            try:
                # Note: session doesn't have a close method outside of context manager
                # For proper cleanup, we would need to reopen the session and then close it
                # using the context manager, but that's beyond the scope of this fix
                logger.info(f"Session {session_name} will be closed on next open")
            except Exception as e:
                logger.error(f"Failed to close session {session_name}: {str(e)}")
            
            # If we have a Flink job ID, also cancel it there
            flink_job_id = task.result.get("flink_job_id")
            if flink_job_id and self.job_manager:
                try:
                    # This would require additional implementation for the actual Flink job cancellation
                    logger.info(f"Cancelling Flink job {flink_job_id}")
                    # TODO: Implement job cancellation via Job Manager API
                except Exception as e:
                    logger.error(f"Failed to cancel Flink job {flink_job_id}: {str(e)}")
            
            task.status = "CANCELLED"
            logger.info(f"Successfully cancelled task {task_id}")
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            task.status = "FAILED"
            task.result["error"] = f"Cancel failed: {str(e)}"
            raise

    async def shutdown(self):
        """Shutdown the runner, cancel all tasks and clean up resources."""
        logger.info("Shutting down Flink SQL Runner")
        
        # Cancel all running tasks
        running_tasks = [task_id for task_id, task in self.tasks.items() 
                         if task.status in ["RUNNING", "PENDING"]]
        
        for task_id in running_tasks:
            try:
                logger.info(f"Cancelling task {task_id} during shutdown")
                await self.cancel(task_id, force=True)
            except Exception as e:
                logger.error(f"Error cancelling task {task_id} during shutdown: {str(e)}")
        
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

    async def _monitor_task(self, task: FlinkSQLTask, session_name: str):
        """
        Monitor the task execution and update status.
        
        Args:
            task: The task instance
            session_name: The SQL Gateway session name
        """
        # Start timeout monitor
        asyncio.create_task(self._task_timeout_monitor(task, task.task_timeout_seconds))
        
        # Monitor the task until it completes or fails
        while task.status in ["RUNNING", "PENDING"]:
            try:
                # Get session
                session = self.sql_gateway_client.get_session(session_name=session_name)
                
                # Check each operation
                for op_handle in task.operation_handles:
                    try:
                        # Create a FlinkOperation with the handle and check status
                        operation = FlinkOperation(session, op_handle)
                        status = operation.status().sync()
                        
                        # If any operation is still running, keep monitoring
                        if status.status in ["RUNNING", "PENDING"]:
                            break
                        
                        # If an operation failed, the whole task failed
                        if status.status == "ERROR":
                            task.status = "FAILED"
                            task.result["error"] = status.error
                            logger.error(f"Task {task.job_id} failed: {status.error}")
                            return
                    except Exception as e:
                        logger.error(f"Error checking operation {op_handle}: {str(e)}")
                
                # If all operations completed successfully, the task is done
                if task.status == "RUNNING":
                    task.status = "COMPLETED"
                    logger.info(f"Task {task.job_id} completed successfully")
                    return
                
                # Wait before checking again
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error monitoring task {task.job_id}: {str(e)}")
                task.status = "FAILED"
                task.result["error"] = str(e)
                return

    async def _task_timeout_monitor(self, task: FlinkSQLTask, timeout_seconds: int):
        """
        Monitor task timeout and cancel if exceeded.
        
        Args:
            task: The task instance
            timeout_seconds: The timeout in seconds
        """
        if timeout_seconds <= 0:
            return
        
        try:
            # Wait for the timeout period
            await asyncio.sleep(timeout_seconds)
            
            # If the task is still running after the timeout, cancel it
            if task.status in ["RUNNING", "PENDING"]:
                logger.warning(f"Task {task.job_id} timed out after {timeout_seconds} seconds")
                task.status = "TIMEOUT"
                task.result["error"] = f"Task timed out after {timeout_seconds} seconds"
                
                # Cancel the task
                await self.cancel(task.job_id, force=True)
        except Exception as e:
            logger.error(f"Error in timeout monitor for task {task.job_id}: {str(e)}")
