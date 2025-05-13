from typing import Dict, List, Optional, Any
import os
import uuid
import tempfile
from datetime import datetime

from resinkit_api.services.agent.task_base import TaskBase
from resinkit_api.db.models import Task
from resinkit_api.core.logging import get_logger

logger = get_logger(__name__)


class FlinkSQLTask(TaskBase):
    """A task class for running Flink SQL jobs via the SQL Gateway."""
    
    def __init__(self, task_type: str = "FLINK_SQL", 
                 name: str = '', 
                 description: str = '', 
                 task_timeout_seconds: int = 3600, 
                 created_at: datetime = datetime.now(),
                 sql_statements: List[str] = None,
                 pipeline_name: str = None,
                 parallelism: int = 1,
                 resources: Dict[str, Any] = None):
        """
        Initialize a Flink SQL task.
        
        Args:
            task_type: The task type identifier
            name: The name of the task
            description: Description of the task
            task_timeout_seconds: Maximum execution time in seconds
            created_at: Task creation timestamp
            sql_statements: List of SQL statements to execute
            pipeline_name: Name of the Flink pipeline
            parallelism: Parallelism setting for the job
            resources: Resource configuration dictionary
        """
        super().__init__(task_type, name, description, task_timeout_seconds, created_at)
        
        # SQL job configuration
        self.sql_statements = sql_statements or []
        
        # Pipeline configuration
        self.pipeline_name = pipeline_name or name
        self.parallelism = parallelism
        
        # Resources
        self.resources = resources or {}
        
        # Task execution state
        self.job_id: Optional[str] = str(uuid.uuid4())
        self.operation_handles: List[str] = []
        self.status = "PENDING"
        self.result: Dict[str, Any] = {}
        
        # Logging
        self.log_file = os.path.join(tempfile.gettempdir(), f"{self.name}_{uuid.uuid4()}.log")
        
    @classmethod
    def from_config(cls, task_config: Dict[str, Any]) -> 'FlinkSQLTask':
        """
        Create a FlinkSQLTask instance from configuration dictionary.
        
        Args:
            task_config: The task configuration dictionary
            
        Returns:
            A new FlinkSQLTask instance
        """
        # Extract basic attributes
        name = task_config.get("name", f"flink_sql_task_{uuid.uuid4()}")
        description = task_config.get("description", "")
        task_timeout_seconds = task_config.get("task_timeout_seconds", 3600)
        
        # Extract SQL job configuration
        job_config = task_config.get("job", {})
        sql_statements = cls._parse_sql_statements(job_config.get("sql", ""))
        
        # Extract pipeline configuration
        pipeline_config = job_config.get("pipeline", {})
        pipeline_name = pipeline_config.get("name", name)
        parallelism = pipeline_config.get("parallelism", 1)
        
        # Extract resources
        resources = task_config.get("resources", {})
        
        return cls(
            task_type="FLINK_SQL",
            name=name,
            description=description,
            task_timeout_seconds=task_timeout_seconds,
            sql_statements=sql_statements,
            pipeline_name=pipeline_name,
            parallelism=parallelism,
            resources=resources
        )
    
    @classmethod
    def from_dao(cls, task_dao: Task) -> 'FlinkSQLTask':
        """
        Create a FlinkSQLTask instance from database Task model.
        
        Args:
            task_dao: The database Task model instance
            
        Returns:
            A new FlinkSQLTask instance
        """
        config = task_dao.config or {}
        job_config = config.get("job", {})
        pipeline_config = job_config.get("pipeline", {})
        
        return cls(
            task_type=task_dao.task_type,
            name=task_dao.name,
            description=task_dao.description,
            task_timeout_seconds=task_dao.task_timeout_seconds,
            created_at=task_dao.created_at,
            sql_statements=cls._parse_sql_statements(job_config.get("sql", "")),
            pipeline_name=pipeline_config.get("name", task_dao.name),
            parallelism=pipeline_config.get("parallelism", 1),
            resources=config.get("resources", {})
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
        string_delimiter = None
        
        for line in sql_text.splitlines():
            line = line.strip()
            if not line or line.startswith('--'):  # Skip empty lines and comments
                continue
                
            current_statement.append(line)
            
            # Check if this line contains a complete statement
            if line.rstrip().endswith(';') and not in_string:
                statements.append('\n'.join(current_statement))
                current_statement = []
                
        # Add the last statement if there's any remaining
        if current_statement:
            statements.append('\n'.join(current_statement))
            
        return statements
    
    def validate(self) -> None:
        """
        Validate the task configuration.
        
        Raises:
            ValueError: If the configuration is invalid
        """
        if not self.sql_statements:
            raise ValueError("No SQL statements found in the task configuration")
        
        # Validate task timeout
        if self.task_timeout_seconds <= 0:
            raise ValueError("Task timeout must be a positive integer")
        
        # Validate parallelism
        if self.parallelism <= 0:
            raise ValueError("Parallelism must be a positive integer")
        
        # Validate resources if specified
        if self.resources:
            self._validate_resources()
    
    def _validate_resources(self) -> None:
        """
        Validate the resources configuration.
        
        Raises:
            ValueError: If the resources configuration is invalid
        """
        # Validate Flink JARs if specified
        if "flink_jars" in self.resources:
            jars = self.resources["flink_jars"]
            if not isinstance(jars, list):
                raise ValueError("flink_jars must be a list")
            
            for jar in jars:
                if not isinstance(jar, dict):
                    raise ValueError("Each jar in flink_jars must be a dictionary")
                
                if "name" not in jar:
                    raise ValueError("Each jar in flink_jars must have a name")
                
                if "location" not in jar and "source" not in jar:
                    raise ValueError("Each jar in flink_jars must have either a location or a source")
