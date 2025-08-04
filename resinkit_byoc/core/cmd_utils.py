"""Command utilities for resinkit_byoc."""

import os
import functools
from typing import Callable, Optional, Union
from pathlib import Path


def idempotent_by(
    file_path: Optional[Union[str, Path]] = None,
    func: Optional[Callable[[], bool]] = None
) -> Callable:
    """
    Decorator that prevents a method from being called based on conditions.
    
    The condition can be either:
    - A file path: if the file exists, the decorated function won't be called
    - A function: if the function returns True, the decorated function won't be called
    
    Args:
        file_path: Path to a file. If exists, prevents function execution.
        func: Function that returns bool. If True, prevents function execution.
        
    Usage:
        @idempotent_by('/opt/setup/.flink_install_state')
        def install_flink():
            # This will only run if the file doesn't exist
            pass
            
        @idempotent_by(func=flink_installed)
        def install_flink():
            # This will only run if flink_installed() returns False
            pass
    
    Raises:
        ValueError: If neither file_path nor func is provided, or if both are provided.
    """
    if file_path is None and func is None:
        raise ValueError("Either file_path or func must be provided")
    
    if file_path is not None and func is not None:
        raise ValueError("Only one of file_path or func should be provided")
    
    def decorator(wrapped_func: Callable) -> Callable:
        @functools.wraps(wrapped_func)
        def wrapper(*args, **kwargs):
            # Check file-based condition
            if file_path is not None:
                if os.path.exists(file_path):
                    print(f"Skipping {wrapped_func.__name__} - state file exists: {file_path}")
                    return None
            
            # Check function-based condition
            if func is not None:
                if func():
                    print(f"Skipping {wrapped_func.__name__} - condition function returned True")
                    return None
            
            # Execute the original function
            try:
                result = wrapped_func(*args, **kwargs)
                
                # Create state file after successful execution (file-based condition only)
                if file_path is not None:
                    # Ensure parent directory exists
                    parent_dir = os.path.dirname(file_path)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                    
                    # Create the state file
                    with open(file_path, 'w') as f:
                        f.write(f"Completed: {wrapped_func.__name__}\n")
                
                return result
            except Exception:
                # Don't create state file if execution failed
                raise
        
        return wrapper
    return decorator