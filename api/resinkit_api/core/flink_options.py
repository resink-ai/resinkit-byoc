from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Type, Optional, Union


@dataclass
class FlinkOption:
    """Class to hold information about a Flink configuration option."""

    key: str
    data_type: Type
    default_value: Any
    description: Optional[str] = None


class FlinkOptions(Enum):
    """
    Enum representing Flink configuration options.
    Each enum value contains the configuration key, expected data type, and default value.
    """

    JAVA_OPTS = FlinkOption(
        key="env.java.opts.all",
        data_type=str,
        default_value="--add-exports=java.base/sun.net.util=ALL-UNNAMED",
        description="Java options for all JVM processes",
    )

    EXECUTION_ATTACHED = FlinkOption(key="execution.attached", data_type=bool, default_value=True, description="Whether the job is submitted in attached mode")

    CHECKPOINTS_DIR = FlinkOption(key="execution.checkpoints.dir", data_type=str, default_value=None, description="Directory to store checkpoints")

    SAVEPOINT_RESTORE_MODE = FlinkOption(key="execution.savepoint-restore-mode", data_type=str, default_value="NO_CLAIM", description="Savepoint restore mode")

    SAVEPOINT_IGNORE_UNCLAIMED_STATE = FlinkOption(
        key="execution.savepoint.ignore-unclaimed-state", data_type=bool, default_value=False, description="Whether to ignore unclaimed state in savepoints"
    )

    SHUTDOWN_ON_ATTACHED_EXIT = FlinkOption(
        key="execution.shutdown-on-attached-exit", data_type=bool, default_value=False, description="Whether to shutdown on attached exit"
    )

    EXECUTION_TARGET = FlinkOption(
        key="execution.target", data_type=str, default_value="remote", description="Execution target (local, remote, kubernetes-session, etc.)"
    )

    JOBMANAGER_BIND_HOST = FlinkOption(key="jobmanager.bind-host", data_type=str, default_value="0.0.0.0", description="Bind host for the JobManager")

    JOBMANAGER_FAILOVER_STRATEGY = FlinkOption(
        key="jobmanager.execution.failover-strategy", data_type=str, default_value="region", description="Failover strategy for the JobManager"
    )

    JOBMANAGER_MEMORY_PROCESS_SIZE = FlinkOption(
        key="jobmanager.memory.process.size", data_type=str, default_value="1600m", description="Total process memory size for the JobManager"
    )

    JOBMANAGER_RPC_ADDRESS = FlinkOption(key="jobmanager.rpc.address", data_type=str, default_value="localhost", description="RPC address for the JobManager")

    JOBMANAGER_RPC_PORT = FlinkOption(key="jobmanager.rpc.port", data_type=int, default_value=6123, description="RPC port for the JobManager")

    PARALLELISM_DEFAULT = FlinkOption(key="parallelism.default", data_type=int, default_value=1, description="Default parallelism for jobs")

    PIPELINE_CLASSPATHS = FlinkOption(key="pipeline.classpaths", data_type=List[str], default_value=[], description="Additional classpath entries for the job")

    PIPELINE_JARS = FlinkOption(key="pipeline.jars", data_type=List[str], default_value=[], description="Additional JAR files for the job")

    REST_ADDRESS = FlinkOption(key="rest.address", data_type=str, default_value="0.0.0.0", description="Address for the REST server")

    REST_BIND_ADDRESS = FlinkOption(key="rest.bind-address", data_type=str, default_value="0.0.0.0", description="Bind address for the REST server")

    SQL_GATEWAY_REST_ADDRESS = FlinkOption(
        key="sql-gateway.endpoint.rest.address", data_type=str, default_value="localhost", description="Address for the SQL Gateway REST endpoint"
    )

    SQL_GATEWAY_REST_PORT = FlinkOption(
        key="sql-gateway.endpoint.rest.port", data_type=int, default_value=8083, description="Port for the SQL Gateway REST endpoint"
    )

    TABLE_CATALOG_STORE_FILE_PATH = FlinkOption(
        key="table.catalog-store.file.path", data_type=str, default_value=None, description="Path for the catalog store file"
    )

    TABLE_CATALOG_STORE_KIND = FlinkOption(key="table.catalog-store.kind", data_type=str, default_value=None, description="Kind of catalog store")

    TABLE_RESOURCES_DOWNLOAD_DIR = FlinkOption(
        key="table.resources.download-dir", data_type=str, default_value=None, description="Directory to download table resources"
    )

    TASKMANAGER_BIND_HOST = FlinkOption(key="taskmanager.bind-host", data_type=str, default_value="0.0.0.0", description="Bind host for the TaskManager")

    TASKMANAGER_MEMORY_PROCESS_SIZE = FlinkOption(
        key="taskmanager.memory.process.size", data_type=str, default_value="4096m", description="Total process memory size for the TaskManager"
    )

    TASKMANAGER_NUMBER_OF_TASK_SLOTS = FlinkOption(
        key="taskmanager.numberOfTaskSlots", data_type=int, default_value=8, description="Number of task slots per TaskManager"
    )

    WORKFLOW_SCHEDULER_TYPE = FlinkOption(key="workflow-scheduler.type", data_type=str, default_value="embedded", description="Type of workflow scheduler")

    def __str__(self) -> str:
        return self.value.key

    @property
    def key(self) -> str:
        """Return the configuration key."""
        return self.value.key

    @property
    def data_type(self) -> Type:
        """Return the expected data type."""
        return self.value.data_type

    @property
    def default_value(self) -> Any:
        """Return the default value."""
        return self.value.default_value

    @property
    def description(self) -> Optional[str]:
        """Return the description."""
        return self.value.description

    def value_of(self, config_dict: dict) -> Any:
        return config_dict.get(self.key)
