from typing import Dict, List, Any
import os
import tempfile
from datetime import datetime


from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.db.models import Task
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class FlinkSQLTask(TaskBase):
    """A task class for running Flink SQL jobs via the SQL Gateway."""

    def __init__(
        self,
        task_id: str,
        name: str,
        description: str = "",
        connection_timeout_seconds: int = 30,
        task_timeout_seconds: int = 3600,
        created_at: datetime = None,
        sql_statements: List[str] = None,
        pipeline_name: str = None,
        parallelism: int = 1,
        resources: Dict[str, Any] = None,
        error_info: Dict[str, Any] = None,
        result_summary: Dict[str, Any] = None,
        execution_details: Dict[str, Any] = None,
        progress_details: Dict[str, Any] = None,
    ):
        super().__init__(
            task_type="flink_sql",
            name=name,
            description=description,
            connection_timeout_seconds=connection_timeout_seconds,
            task_timeout_seconds=task_timeout_seconds,
            task_id=task_id,
            created_at=created_at,
            error_info=error_info,
            result_summary=result_summary,
            execution_details=execution_details,
            progress_details=progress_details,
        )
        self.sql_statements = sql_statements or []
        self.pipeline_name = pipeline_name or name
        self.parallelism = parallelism
        self.resources = resources or {}
        self.operation_handles: List[str] = []
        self.result: Dict[str, Any] = {}
        self.log_file = os.path.join(tempfile.gettempdir(), f"{self.task_id}.log")

    @classmethod
    def from_dao(cls, task_dao: Task, variables: Dict[str, Any] | None = None) -> "FlinkSQLTask":
        # Get submitted configs and apply variable substitution if needed
        config = task_dao.submitted_configs or {}
        if variables and config:
            config = TaskBase.render_with_variables(config, variables)

        job_config = config.get("job", {})
        connection_timeout_seconds = config.get("connection_timeout_seconds", 30)
        # recalculate task timeout seconds based on expires_at
        task_timeout_seconds = (task_dao.expires_at - task_dao.created_at).total_seconds() if task_dao.expires_at else 3600
        pipeline_config = job_config.get("pipeline", {})

        return cls(
            task_id=task_dao.task_id,
            name=task_dao.task_name,
            description=task_dao.description,
            connection_timeout_seconds=connection_timeout_seconds,
            task_timeout_seconds=task_timeout_seconds,
            created_at=task_dao.created_at,
            sql_statements=cls._parse_sql_statements(job_config.get("sql", "")),
            pipeline_name=pipeline_config.get("name", task_dao.task_name),
            parallelism=pipeline_config.get("parallelism", 1),
            resources=config.get("resources", {}),
            error_info=task_dao.error_info,
            result_summary=task_dao.result_summary,
            execution_details=task_dao.execution_details,
            progress_details=task_dao.progress_details,
        )

    @staticmethod
    def _parse_sql_statements(sql_text: str) -> List[str]:
        """
        Parse the SQL text into individual SQL statements.

        Args:
            sql_text: The SQL text from the configuration

        Returns:
            A list of individual SQL statements
        """
        if not sql_text:
            return []

        # Split by semicolons, but handle semicolons within quotes/strings
        statements = []
        current_statement = []
        in_string = False

        for line in sql_text.splitlines():
            line = line.strip()
            if not line or line.startswith("--"):  # Skip empty lines and comments
                continue

            current_statement.append(line)

            # Check if this line contains a complete statement
            if line.rstrip().endswith(";") and not in_string:
                statements.append("\n".join(current_statement))
                current_statement = []

        # Add the last statement if there's any remaining
        if current_statement:
            statements.append("\n".join(current_statement))

        return statements

    @classmethod
    def validate(cls, config: dict) -> None:
        """
        Validate the FlinkSQLTask configuration dictionary.
        Raises:
            ValueError: If the configuration is invalid
        """
        # Extract SQL statements from nested job.sql
        job = config.get("job", {})
        sql_text = job.get("sql", "")
        sql_statements = cls._parse_sql_statements(sql_text)
        if not sql_statements:
            raise ValueError("No SQL statements found in the task configuration (expected under job.sql)")

        # Extract parallelism from job.pipeline.parallelism
        pipeline = job.get("pipeline", {})
        parallelism = pipeline.get("parallelism", 1)
        if parallelism <= 0:
            raise ValueError("Parallelism must be a positive integer (expected under job.pipeline.parallelism)")

        # Extract task_timeout_seconds from top-level
        if config.get("task_timeout_seconds", 3600) <= 0:
            raise ValueError("Task timeout must be a positive integer")

        # Extract resources from top-level
        resources = config.get("resources", {})
        if resources:
            cls._validate_resources(resources)

    @staticmethod
    def _validate_resources(resources: dict) -> None:
        if "flink_jars" in resources:
            jars = resources["flink_jars"]
            if not isinstance(jars, list):
                raise ValueError("flink_jars must be a list")
            for jar in jars:
                if not isinstance(jar, dict):
                    raise ValueError("Each jar in flink_jars must be a dictionary")
                if "name" not in jar:
                    raise ValueError("Each jar in flink_jars must have a name")
                if "location" not in jar and "source" not in jar:
                    raise ValueError("Each jar in flink_jars must have either a location or a source")
