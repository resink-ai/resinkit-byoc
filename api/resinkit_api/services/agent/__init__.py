"""
Agent Service Initialization

This module initializes and exports the components of the agent service.
It creates instances of task runners, registers them with the registry,
and provides a clean API for the rest of the application.
"""

from typing import Optional

from resinkit_api.core.logging import get_logger
from resinkit_api.services import get_service_manager
from resinkit_api.services.agent.runner_registry import TASK_RUNNER_REGISTRY, register_runner, get_runner_for_task_type
from resinkit_api.services.agent.flink.flink_cdc_pipeline_runner import FlinkCdcPipelineRunner
from resinkit_api.clients.job_manager.flink_job_manager_client import FlinkJobManager
from resinkit_api.clients.sql_gateway.flink_sql_gateway_client import FlinkSqlGatewayClient
from resinkit_api.services.svc_manager import SvcManager

logger = get_logger(__name__)

# Singleton instances
_service_manager: Optional[SvcManager] = None
_initialized = False


def get_job_manager() -> FlinkJobManager:
    return get_service_manager().job_manager


def get_sql_gateway() -> FlinkSqlGatewayClient:
    return get_service_manager().sql_gateway


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
        job_manager = get_job_manager()
        sql_gateway = get_sql_gateway()
        runner = FlinkCdcPipelineRunner(job_manager, sql_gateway)
        register_runner("flink_cdc_pipeline", runner)
        logger.info("Registered FlinkCdcPipelineRunner")
    
    _initialized = True
    logger.info("Agent service initialization complete")


# Initialize the agent service when the module is imported
initialize_agent_service()

# Export the public components
__all__ = ["get_runner_for_task_type", "register_runner", "get_job_manager", "get_sql_gateway", "initialize_agent_service"]
