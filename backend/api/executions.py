"""
Executions API endpoints.

This router exposes endpoints for starting a code generation execution and
checking its status. Executions are simulated for demo purposes using
background tasks and the `ConnectionManager` to broadcast progress updates via
WebSocket. In production, this would invoke real AI agents and persist
execution state to a database.
"""

import uuid
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from ..services.auth_service import get_current_user, User
from ..services.websocket_manager import connection_manager


router = APIRouter(prefix="/executions", tags=["Executions"])


class ExecutionRequest(BaseModel):
    template_id: str
    description: str
    team_config: str = "compact"
    budget_usd: float = 10.0


class ExecutionResponse(BaseModel):
    execution_id: str
    status: str
    estimated_duration_minutes: int
    estimated_cost_usd: float
    websocket_url: str


# In-memory execution store for the demo. In real use, store in DB.
executions_store: dict[str, dict[str, Any]] = {}


@router.post("/start", response_model=ExecutionResponse)
async def start_execution(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> ExecutionResponse:
    """Start a new code generation execution and return its initial status."""
    execution_id = str(uuid.uuid4())

    # Persist initial execution info
    executions_store[execution_id] = {
        "user_id": current_user.id,
        "template_id": request.template_id,
        "description": request.description,
        "status": "queued",
        "progress": 0.0,
    }

    # Notify clients that execution has started
    background_tasks.add_task(
        connection_manager.send_execution_started,
        execution_id,
        request.template_id,
        request.team_config,
    )

    # Simulate execution progress in the background
    background_tasks.add_task(simulate_execution_progress, execution_id)

    return ExecutionResponse(
        execution_id=execution_id,
        status="queued",
        estimated_duration_minutes=45,
        estimated_cost_usd=2.5,
        websocket_url=f"/ws/{execution_id}",
    )


async def simulate_execution_progress(execution_id: str) -> None:
    """Simulate execution progress and broadcast updates at regular intervals."""
    import asyncio
    phases = [
        ("planning", 0.2),
        ("architecture", 0.4),
        ("development", 0.7),
        ("testing", 0.9),
        ("completed", 1.0),
    ]
    for phase, progress in phases:
        await asyncio.sleep(3)
        # Update in-memory store
        if execution_id in executions_store:
            executions_store[execution_id]["status"] = phase
            executions_store[execution_id]["progress"] = progress
        # Broadcast progress
        await connection_manager.send_progress_update(
            execution_id,
            progress,
            phase,
            {"tokens_used": int(progress * 1000), "cost_usd": progress * 2.5},
        )
        await connection_manager.send_log_message(
            execution_id,
            phase.replace("_", " "),
            "info",
            f"Phase {phase} - {progress * 100:.1f}% complete",
        )


@router.get("/{execution_id}/status")
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Return the current status of a given execution."""
    if execution_id not in executions_store:
        raise HTTPException(status_code=404, detail="Execution not found")
    execution = executions_store[execution_id]
    if execution["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return execution