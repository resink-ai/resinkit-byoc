"""
Task Runner Registry

This module provides a registry for mapping task types to their respective runner classes.
It allows the system to dynamically select the appropriate runner for a given task type.
"""

from typing import Dict

from resinkit_api.core.logging import get_logger
from resinkit_api.services.agent.task_runner_base import TaskRunnerBase

logger = get_logger(__name__)

# A registry mapping task types to their respective runner instances
TASK_RUNNER_REGISTRY: Dict[str, TaskRunnerBase] = {}


def get_runner_for_task_type(task_type: str) -> TaskRunnerBase:
    """
    Get an instance of the appropriate task runner for a given task type.

    Args:
        task_type: The type of task to get a runner for
    Returns:
        An instance of a TaskRunnerBase subclass

    Raises:
        ValueError: If no runner is registered for the given task type
    """
    if task_type not in TASK_RUNNER_REGISTRY:
        logger.error(f"No runner registered for task type: {task_type}")
        raise ValueError(f"No runner registered for task type: {task_type}")

    return TASK_RUNNER_REGISTRY[task_type]


def register_runner(task_type: str, runner: TaskRunnerBase) -> None:
    """
    Register a new task runner for a given task type.

    Args:
        task_type: The type of task this runner handles
        runner: The runner instance to register

    Raises:
        TypeError: If runner_class is not a subclass of TaskRunnerBase
    """
    if not isinstance(runner, TaskRunnerBase):
        raise TypeError(f"Runner must be a subclass of TaskRunnerBase, got {runner}")

    TASK_RUNNER_REGISTRY[task_type] = runner
    logger.info(f"Registered {runner.__class__.__name__} for task type: {task_type}")
