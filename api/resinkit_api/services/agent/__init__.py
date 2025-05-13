"""
Agent Service Initialization

This module initializes and exports the components of the agent service.
It creates instances of task runners, registers them with the registry,
and provides a clean API for the rest of the application.
"""

from typing import Optional

from resinkit_api.core.logging import get_logger
from resinkit_api.services import get_service_manager
from resinkit_api.services.agent.flink.flink_sql_runner import FlinkSQLRunner
from resinkit_api.services.agent.runner_registry import TASK_RUNNER_REGISTRY, register_runner, get_runner_for_task_type
from resinkit_api.services.agent.flink.flink_cdc_pipeline_runner import FlinkCdcPipelineRunner
from resinkit_api.services.agent.tasks import TaskManager

logger = get_logger(__name__)

# Singleton instances
_flink_cdc_pipeline_runner: Optional[FlinkCdcPipelineRunner] = None
_flink_sql_runner: Optional[FlinkSQLRunner] = None
_task_manager: Optional[TaskManager] = None
_initialized = False


def get_flink_cdc_pipeline_runner() -> FlinkCdcPipelineRunner:
    global _flink_cdc_pipeline_runner
    if _flink_cdc_pipeline_runner is None:
        _flink_cdc_pipeline_runner = FlinkCdcPipelineRunner(job_manager=get_service_manager().job_manager, sql_gateway_client=get_service_manager().sql_gateway)
    return _flink_cdc_pipeline_runner


def get_flink_sql_runner() -> FlinkSQLRunner:
    global _flink_sql_runner
    if _flink_sql_runner is None:
        _flink_sql_runner = FlinkSQLRunner(job_manager=get_service_manager().job_manager, sql_gateway_client=get_service_manager().sql_gateway)
    return _flink_sql_runner


def get_task_manager() -> TaskManager:
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


def initialize_agent_service() -> None:
    """
    Initialize the agent service components.
    This function registers all task runners and initializes dependencies.
    It's designed to be called only once during application startup.
    """
    global _initialized

    if _initialized:
        logger.info("Agent service already initialized, skipping initialization")
        return

    # Register predefined runners
    # This will load built-in runner types from the registry module,
    logger.info("Registering task runners")
    # Check if the FlinkCdcPipelineRunner is already registered
    if "flink_cdc_pipeline" in TASK_RUNNER_REGISTRY:
        logger.debug("FlinkCdcPipelineRunner already registered")
    else:
        # Create a new runner with services from the service manager
        register_runner("flink_cdc_pipeline", get_flink_cdc_pipeline_runner())
        register_runner("flink_sql", get_flink_sql_runner())
        logger.info("Registered FlinkCdcPipelineRunner")

    _initialized = True
    logger.info("Agent service initialization complete")


# Initialize the agent service when the module is imported
initialize_agent_service()

# Export the public components
__all__ = ["get_runner_for_task_type", "register_runner", "initialize_agent_service", "get_flink_cdc_pipeline_runner", "get_task_manager"]
