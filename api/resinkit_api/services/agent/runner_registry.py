"""
Task Runner Registry

This module provides a registry for mapping task types to their respective runner classes.
It allows the system to dynamically select the appropriate runner for a given task type.
"""

from typing import Dict, Type

from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase
from resinkit_api.services.agent.flink.flink_cdc_pipeline_runner import FlinkCdcPipelineRunner

logger = get_logger(__name__)

# A registry mapping task types to their respective runner classes
TASK_RUNNER_REGISTRY: Dict[str, Type[TaskRunnerBase]] = {
    "flink_cdc_pipeline": FlinkCdcPipelineRunner,
}

def get_runner_for_task_type(task_type: str, runtime_env: dict = None) -> TaskRunnerBase:
    """
    Get an instance of the appropriate task runner for a given task type.
    
    Args:
        task_type: The type of task to get a runner for
        runtime_env: Optional runtime environment configuration
        
    Returns:
        An instance of a TaskRunnerBase subclass
        
    Raises:
        ValueError: If no runner is registered for the given task type
    """
    if task_type not in TASK_RUNNER_REGISTRY:
        logger.error(f"No runner registered for task type: {task_type}")
        raise ValueError(f"No runner registered for task type: {task_type}")
    
    runner_class = TASK_RUNNER_REGISTRY[task_type]
    logger.debug(f"Using {runner_class.__name__} for task type: {task_type}")
    
    return runner_class(runtime_env or {})

def register_runner(task_type: str, runner_class: Type[TaskRunnerBase]) -> None:
    """
    Register a new task runner for a given task type.
    
    Args:
        task_type: The type of task this runner handles
        runner_class: The class of the runner (must be a TaskRunnerBase subclass)
        
    Raises:
        TypeError: If runner_class is not a subclass of TaskRunnerBase
    """
    if not issubclass(runner_class, TaskRunnerBase):
        raise TypeError(f"Runner class must be a subclass of TaskRunnerBase, got {runner_class}")
    
    TASK_RUNNER_REGISTRY[task_type] = runner_class
    logger.info(f"Registered {runner_class.__name__} for task type: {task_type}") 