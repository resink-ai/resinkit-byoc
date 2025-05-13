from fastapi import APIRouter, HTTPException, status, Body, Query, Path
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import yaml
from resinkit_api.services.agent import tasks as agent_tasks_service

router = APIRouter()

# 1. Submit a new Task
@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def submit_task(payload: dict = Body(...)):
    try:
        result = await agent_tasks_service.submit_task(payload)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=result)
    except agent_tasks_service.InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except agent_tasks_service.UnprocessableTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# New endpoint for YAML task submission
@router.post("/tasks/yaml", status_code=status.HTTP_202_ACCEPTED)
async def submit_task_yaml(yaml_payload: str = Body(..., media_type="text/plain")):
    try:
        # Convert YAML to dictionary
        payload = yaml.safe_load(yaml_payload)
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Invalid YAML: must represent a dictionary")
        
        # Process the payload same as the regular submit_task endpoint
        result = await agent_tasks_service.submit_task(payload)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=result)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
    except agent_tasks_service.InvalidTaskError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except agent_tasks_service.UnprocessableTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 2. Get Task Details
@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str = Path(...)):
    try:
        return await agent_tasks_service.get_task_details(task_id)
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
):
    try:
        return await agent_tasks_service.list_tasks(
            task_type, status_, task_name_contains, tags_include_any,
            created_after, created_before, limit, page_token, sort_by, sort_order
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 4. Cancel a Task
@router.post("/tasks/{task_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_task(
    task_id: str = Path(...),
    force: bool = Query(False, description="Whether to forcefully cancel the task")
):
    try:
        result = await agent_tasks_service.cancel_task(task_id, force=force)
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content=result)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except agent_tasks_service.UnprocessableTaskError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 5. Get Task Logs
@router.get("/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: str = Path(...),
    level: str = Query("INFO", description="Log level filter (INFO, WARN, ERROR, DEBUG)")
):
    try:
        logs = await agent_tasks_service.get_task_logs(task_id, level=level)
        return StreamingResponse(
            content=iter([logs.encode()]), 
            media_type="text/plain"
        )
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

# 6. Get Task Results
@router.get("/tasks/{task_id}/results")
async def get_task_results(task_id: str = Path(...)):
    try:
        return await agent_tasks_service.get_task_results(task_id)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
