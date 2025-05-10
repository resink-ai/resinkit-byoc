from fastapi import APIRouter, HTTPException, Request, status, Body, Query, Path, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List
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
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 2. Get Task Details
@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str = Path(...)):
    try:
        return await agent_tasks_service.get_task_details(task_id)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

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
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 4. Cancel a Task
@router.post("/tasks/{task_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
async def cancel_task(task_id: str = Path(...), payload: dict = Body(None)):
    try:
        return await agent_tasks_service.cancel_task(task_id, payload)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except agent_tasks_service.TaskConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 5. Get Task Logs
@router.get("/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: str = Path(...),
    log_type: Optional[str] = Query(None),
    since_timestamp: Optional[str] = Query(None),
    since_token: Optional[str] = Query(None),
    limit_lines: Optional[int] = Query(1000, ge=1, le=10000),
    stream: Optional[bool] = Query(False),
    log_level_filter: Optional[str] = Query(None),
):
    try:
        if stream:
            return await agent_tasks_service.stream_task_logs(
                task_id, log_type, since_timestamp, since_token, limit_lines, log_level_filter
            )
        else:
            return await agent_tasks_service.get_task_logs(
                task_id, log_type, since_timestamp, since_token, limit_lines, log_level_filter
            )
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 6. Get Task Results
@router.get("/tasks/{task_id}/results")
async def get_task_results(task_id: str = Path(...)):
    try:
        return await agent_tasks_service.get_task_results(task_id)
    except agent_tasks_service.TaskNotFoundError:
        raise HTTPException(status_code=404, detail="Task not found")
    except agent_tasks_service.TaskConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal Server Error") 