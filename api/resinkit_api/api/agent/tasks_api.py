from fastapi import APIRouter, HTTPException, status, Body, Query, Path, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
import yaml
from resinkit_api.services.agent import get_task_manager, tasks as agent_tasks_service
from resinkit_api.services.agent.data_models import TaskConflictError, TaskNotFoundError
from resinkit_api.services.agent.tasks import TaskManager, TaskResult
from resinkit_api.services.agent.task_runner_base import LogEntry
from resinkit_api.core.logging import get_logger
from sqlalchemy.orm import Session
from resinkit_api.db.database import get_db
from resinkit_api.db import variables_crud
from pydantic import BaseModel

logger = get_logger(__name__)

router = APIRouter()


# Variable models
class VariableCreate(BaseModel):
    name: str
    value: str
    description: Optional[str] = None


class VariableResponse(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    created_by: str


class VariableUpdate(BaseModel):
    value: Optional[str] = None
    description: Optional[str] = None


# Variable API endpoints
@router.post("/variables", status_code=status.HTTP_201_CREATED, response_model=VariableResponse)
async def create_variable(
    variable: VariableCreate,
    db: Session = Depends(get_db),
    created_by: str = "user",  # In a real app, get this from auth
):
    """Create a new variable with encrypted value"""
    try:
        # Check if variable already exists
        existing = await variables_crud.get_variable(db, variable.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Variable with name '{variable.name}' already exists")

        # Create new variable
        result = await variables_crud.create_variable(db=db, name=variable.name, value=variable.value, description=variable.description, created_by=created_by)

        # Return response without the encrypted value
        return VariableResponse(
            name=result.name,
            description=result.description,
            created_at=result.created_at.isoformat(),
            updated_at=result.updated_at.isoformat(),
            created_by=result.created_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create variable: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/variables", response_model=List[VariableResponse])
async def list_variables(db: Session = Depends(get_db)):
    """List all variables (without their values)"""
    try:
        variables = await variables_crud.list_variables(db)

        # Convert to response model
        return [
            VariableResponse(
                name=var.name,
                description=var.description,
                created_at=var.created_at.isoformat(),
                updated_at=var.updated_at.isoformat(),
                created_by=var.created_by,
            )
            for var in variables
        ]
    except Exception as e:
        logger.error(f"Failed to list variables: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.get("/variables/{name}", response_model=VariableResponse)
async def get_variable(name: str, db: Session = Depends(get_db)):
    """Get a variable by name (without its value)"""
    try:
        variable = await variables_crud.get_variable(db, name)
        if not variable:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variable with name '{name}' not found")

        # Return response without the encrypted value
        return VariableResponse(
            name=variable.name,
            description=variable.description,
            created_at=variable.created_at.isoformat(),
            updated_at=variable.updated_at.isoformat(),
            created_by=variable.created_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get variable: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.put("/variables/{name}", response_model=VariableResponse)
async def update_variable(name: str, variable_update: VariableUpdate, db: Session = Depends(get_db)):
    """Update a variable by name"""
    try:
        # Check if variable exists
        existing = await variables_crud.get_variable(db, name)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variable with name '{name}' not found")

        # Update variable
        result = await variables_crud.update_variable(db=db, name=name, value=variable_update.value, description=variable_update.description)

        # Return response without the encrypted value
        return VariableResponse(
            name=result.name,
            description=result.description,
            created_at=result.created_at.isoformat(),
            updated_at=result.updated_at.isoformat(),
            created_by=result.created_by,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update variable: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.delete("/variables/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variable(name: str, db: Session = Depends(get_db)):
    """Delete a variable by name"""
    try:
        # Check if variable exists
        existing = await variables_crud.get_variable(db, name)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Variable with name '{name}' not found")

        # Delete variable
        await variables_crud.delete_variable(db, name)

        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete variable: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# 1. Submit a new Task with variable resolution
@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def submit_task(payload: dict = Body(...), task_manager: TaskManager = Depends(get_task_manager), db: Session = Depends(get_db)):
    try:
        # Process payload for variable substitution if it contains string fields
        processed_payload = await process_payload_variables(payload, db)

        # Submit the processed task
        result = await task_manager.submit_task(processed_payload)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=result)
    except agent_tasks_service.InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except agent_tasks_service.UnprocessableTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# Process payload variables recursively
async def process_payload_variables(payload: Dict, db: Session) -> Dict:
    """
    Process payload to replace variable references with their values.
    Handles nested dictionaries and lists.
    """
    if isinstance(payload, dict):
        return {k: await process_payload_variables(v, db) for k, v in payload.items()}
    elif isinstance(payload, list):
        return [await process_payload_variables(item, db) for item in payload]
    elif isinstance(payload, str):
        # Replace variables in strings
        return await variables_crud.resolve_variables(db, payload)
    else:
        # Return other types as is
        return payload


# New endpoint for YAML task submission with variable resolution
@router.post("/tasks/yaml", status_code=status.HTTP_202_ACCEPTED)
async def submit_task_yaml(
    yaml_payload: str = Body(..., media_type="text/plain"), task_manager: TaskManager = Depends(get_task_manager), db: Session = Depends(get_db)
):
    try:
        # Process YAML string for variable substitution
        processed_yaml = await variables_crud.resolve_variables(db, yaml_payload)

        # Convert YAML to dictionary
        payload = yaml.safe_load(processed_yaml)
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Invalid YAML: must represent a dictionary")

        # Submit the processed task
        result = await task_manager.submit_task(payload)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=result)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
    except agent_tasks_service.InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except agent_tasks_service.UnprocessableTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# 2. Get Task Details
@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str = Path(...), task_manager: TaskManager = Depends(get_task_manager)):
    try:
        return await task_manager.get_task_details(task_id)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# 3. List Tasks
@router.get("/tasks")
async def list_tasks(
    task_type: Optional[str] = Query(None),
    status_: Optional[str] = Query(None, alias="status"),
    task_name_contains: Optional[str] = Query(None),
    tags_include_any: Optional[str] = Query(None),
    created_after: Optional[str] = Query(None),
    created_before: Optional[str] = Query(None),
    limit: Optional[int] = Query(20, ge=1, le=100),
    page_token: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    task_manager: TaskManager = Depends(get_task_manager),
):
    try:
        return await task_manager.list_tasks(
            task_type, status_, task_name_contains, tags_include_any, created_after, created_before, limit, page_token, sort_by, sort_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# 4. Cancel a Task
@router.post("/tasks/{task_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_task(
    task_id: str = Path(...),
    force: bool = Query(False, description="Whether to forcefully cancel the task"),
    task_manager: TaskManager = Depends(get_task_manager),
):
    try:
        result = await task_manager.cancel_task(task_id, force=force)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=result)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except TaskConflictError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except agent_tasks_service.UnprocessableTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# 5. Get Task Logs
@router.get("/tasks/{task_id}/logs", response_model=List[LogEntry])
async def get_task_logs(
    task_id: str = Path(...),
    level: str = Query("INFO", description="Log level filter (INFO, WARN, ERROR, DEBUG)"),
    task_manager: TaskManager = Depends(get_task_manager),
):
    try:
        logs = await task_manager.get_task_logs(task_id, log_level_filter=level)
        return logs
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# 6. Get Task Results
@router.get("/tasks/{task_id}/results", response_model=TaskResult)
async def get_task_results(task_id: str = Path(...), task_manager: TaskManager = Depends(get_task_manager)):
    try:
        return await task_manager.get_task_results(task_id)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# New endpoint: Permanently delete a task and its events if in end state
@router.delete("/tasks/{task_id}/permanent", status_code=status.HTTP_200_OK)
async def permanently_delete_task(
    task_id: str = Path(...),
    db: Session = Depends(get_db),
    task_manager: TaskManager = Depends(get_task_manager),
):
    """Permanently delete a task and its events if the task is in an end state (COMPLETED, FAILED, CANCELLED, or expired)."""
    try:
        task_manager.permanently_delete_task(task_id, db)
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Task permanently deleted"})
    except TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except TaskConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
