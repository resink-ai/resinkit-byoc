import os
from typing import Any, Dict, List, Optional

from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.clients.sql_gateway.flink_sql_gateway_client import FlinkSqlGatewayClient
from resinkit_api.clients.sql_gateway.flink_operation import FlinkOperation
from resinkit_api.core.logging import get_logger
from resinkit_api.db.models import Task, TaskStatus
from resinkit_api.services.agent.flink.flink_resource_manager import FlinkResourceManager
from resinkit_api.services.agent.flink.flink_sql_task import FlinkSQLTask
from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase
from resinkit_api.services.agent.task_status_persistence import TaskStatusPersistenceMixin

logger = get_logger(__name__)


class FlinkSQLRunner(TaskRunnerBase, TaskStatusPersistenceMixin):
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
            FlinkSQLTask.validate(task_config)
        except Exception as e:
            raise ValueError(f"Invalid Flink SQL configuration: {str(e)}")

    def from_dao(self, dao: Task) -> FlinkSQLTask:
        """
        Create a FlinkSQLRunner instance from a Task DAO.
        
        Args:
            dao: The Task DAO
            
        Returns:
            The FlinkSQLRunner instance
        """
        return FlinkSQLTask.from_dao(dao)


    async def submit_task(self, task: FlinkSQLTask) -> FlinkSQLTask:
        """
        Submits a Flink SQL job to the SQL Gateway.
        
        Args:
            task: The task instance
            
        Returns:
            The created task instance
            
        Raises:
            Exception: If job submission fails
        """
        task_id = task.task_id
        self.tasks[task_id] = task
        
        # Process resources
        resources = await self.resource_manager.process_resources(task.resources)
        
        try:
            # TODO: create a LogManager class to handle task logs, flink job logs, etc.
            # Open log file for the task
            log_file = open(task.log_file, "w")
            # Update task status
            task.status = TaskStatus.RUNNING
            await self.persist_task_status(task, TaskStatus.RUNNING)
            log_file.write(f"Starting Flink SQL job: {task.name}\n")
            
            # Create session properties
            session_properties = self._create_session_properties(task, resources)
            session_name = f"session_{task_id}"
            
            # Create and open a session; no need to close it, going to reuse it
            session = self.sql_gateway_client.get_session(
                properties=session_properties, 
                session_name=session_name,
                create_if_not_exist=True,
            )
            
            log_file.write(f"Created Flink SQL session: {session_name}\n")
            
            # Execute each SQL statement
            operation_handles = []
            for i, sql in enumerate(task.sql_statements):
                log_file.write(f"Executing SQL statement {i+1}/{len(task.sql_statements)}\n")
                log_file.write(f"SQL: {sql}\n")
                flink_job_id = None

                # Execute the statement
                with session.execute(sql).sync() as operation:
                    # Store the operation handle for later status checks
                    operation_handles.append(operation.operation_handle)
                    
                    # For SELECT statements, fetch and display results
                    if sql.strip().upper().startswith("SELECT"):
                        result_df = operation.fetch().sync()
                        log_file.write(f"Results: {result_df.to_string()}\n")
                        if not task.result.get("results"):
                            task.result["results"] = []
                        task.result["results"].append(result_df.to_json(orient="records", date_format="iso"))
                    
                    # Get the operation status
                    status = operation.status().sync()
                    log_file.write(f"Operation status: {status.status}\n")
                    
                    # If this is a job submission, extract the job ID
                    if "jobId" in status.to_dict():
                        flink_job_id = status.to_dict()["jobId"]
                        log_file.write(f"Flink job ID: {flink_job_id}\n")
                        task.result["flink_job_id"] = flink_job_id
                        self.job_id_to_task_id[flink_job_id] = task_id
                    
            # Store the operation handles
            task.operation_handles = operation_handles
            task.result["operation_handles"] = operation_handles
            task.result["session_name"] = session_name
            
            # Store the session name
            self.session_to_task_id[session_name] = task_id
            
            log_file.write(f"Flink SQL job submitted successfully, name: {task.name}, id: {task.task_id}")
            
            return task
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.result = {"error": str(e)}
            log_file.write(f"Failed to submit Flink SQL job: {str(e)}\n")
            logger.error(f"Failed to submit Flink SQL job: {str(e)}", exc_info=True)
            await self.persist_task_status(task, TaskStatus.FAILED, str(e))
            raise
        finally:
            log_file.close()

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

    def get_log_summary(self, task: FlinkSQLTask, level: str = "INFO") -> str:
        """
        Gets a summary of logs for a Flink SQL job.
        
        Args:
            task: The task instance
            level: The log level to filter by
            
        Returns:
            A summary of logs
        """
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
            logger.error(f"Failed to read logs for task {task.task_id}: {str(e)}")
            return f"Error reading logs: {str(e)}"

    async def cancel(self, task: FlinkSQLTask, force: bool = False):
        """
        Cancels a running Flink SQL job.
        
        Args:
            task: The task instance
            force: Whether to force cancel the job
        """
        if not task:
            logger.warning(f"Task {task.task_id} not found")
            return
        
        if task.status not in [TaskStatus.RUNNING, TaskStatus.PENDING]:
            logger.info(f"Task {task.task_id} is not running, current status: {task.status.value}")
            return
        
        task.status = TaskStatus.CANCELLING
        await self.persist_task_status(task, TaskStatus.CANCELLING)
        
        try:
            # Get session name
            session_name = task.result.get("session_name")
            if not session_name:
                logger.warning(f"No session name found for task {task.task_id}")
                return
            
            # Get session
            with self.sql_gateway_client.get_session(session_name=session_name, create_if_not_exist=False) as session:
                if not session.was_alive:
                    logger.warning(f"Session {session_name} was not alive when cancelling task {task.task_id}, consider task completed")
                    await self.persist_task_status(task, TaskStatus.COMPLETED, f"Session {session_name} was not alive")
                    return
                
                # Cancel each operation
                for op_handle in task.operation_handles:
                    try:
                        async with FlinkOperation(session, op_handle) as operation:
                            response = await operation.cancel().asyncio()
                            logger.info(f"Cancelled operation {op_handle} for task {task.task_id}, response: {response}")
                    except Exception as e:
                        logger.error(f"Failed to cancel operation {op_handle}: {str(e)}")
                
                task.status = TaskStatus.CANCELLED
                logger.info(f"Successfully cancelled task {task.task_id}")
                await self.persist_task_status(task, TaskStatus.CANCELLED)
        except Exception as e:
            logger.error(f"Failed to cancel task {task.task_id}: {str(e)}")
            task.status = TaskStatus.FAILED
            task.result["error"] = f"Cancel failed: {str(e)}"
            await self.persist_task_status(task, TaskStatus.FAILED, f"Cancel failed: {str(e)}")
            raise

    async def shutdown(self):
        """Shutdown the runner, cancel all tasks and clean up resources."""
        logger.info("Shutting down Flink SQL Runner")
        
        # Cancel all running tasks
        running_tasks = [task_id for task_id, task in self.tasks.items() 
                         if task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]]
        
        for task_id in running_tasks:
            try:
                logger.info(f"Cancelling task {task_id} during shutdown")
                await self.cancel(self.tasks[task_id], force=True)
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

    async def fetch_task_status(self, task: FlinkSQLTask) -> FlinkSQLTask:
        """
        Fetches the latest status of a Flink SQL task.
        
        Args:
            task: The task instance
            
        Returns:
            An updated task instance with the latest status
        """
        if not task:
            logger.warning(f"Task {task.task_id} not found")
            return None
        
        # Get session name
        session_name = task.result.get("session_name")
        
        # Initialize status as the current task status
        new_status = task.status
        error_message = None
        
        if session_name:
            try:
                # Get session
                session = self.sql_gateway_client.get_session(
                    session_name=session_name,
                    create_if_not_exist=False
                )
                
                if not session.was_alive:
                    logger.info(f"Session {session_name} was not alive for task {task.task_id}, consider task completed")
                    new_status = TaskStatus.COMPLETED
                else:
                    # Check each operation
                    operations_running = False
                    operations_failed = False
                    operations_error = None
                    
                    for op_handle in task.operation_handles:
                        try:
                            # Create a FlinkOperation with the handle and check status
                            operation = FlinkOperation(session, op_handle)
                            status = operation.status().sync()
                            
                            # If any operation is still running, keep monitoring
                            if status.status in ["RUNNING", "PENDING"]:
                                operations_running = True
                                break
                            
                            # If an operation failed, the whole task failed
                            if status.status == "ERROR":
                                operations_failed = True
                                operations_error = status.error
                                break
                        except Exception as e:
                            logger.error(f"Error checking operation {op_handle}: {str(e)}")
                            operations_failed = True
                            operations_error = str(e)
                            break
                    
                    # Update status based on operations
                    if operations_failed:
                        new_status = TaskStatus.FAILED
                        error_message = operations_error
                    elif not operations_running and new_status == TaskStatus.RUNNING:
                        new_status = TaskStatus.COMPLETED
            except Exception as e:
                logger.error(f"Error fetching status for task {task.task_id}: {str(e)}")
                new_status = TaskStatus.FAILED
                error_message = str(e)
        
        # Update task status if changed
        if new_status != task.status:
            task.status = new_status
            if new_status == TaskStatus.FAILED and error_message:
                task.result = task.result or {}
                task.result["error"] = error_message
        
        return task
