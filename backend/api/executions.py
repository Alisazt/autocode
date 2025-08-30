"""
Execution API for starting and monitoring project runs.

This module defines REST endpoints for creating new executions
within the AutoDev system. When a client requests a new execution
the orchestrator is invoked asynchronously and the execution ID
is returned immediately. Clients can then subscribe to real‑time
events via the WebSocket endpoint to monitor progress.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request

# Note: Authentication is disabled in this demo. In a production
# deployment you would import and use get_current_active_user from
# backend.services.auth_service to secure execution endpoints.

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("/start")
async def start_execution(request: Request, body: Dict[str, Any]) -> Dict[str, Any]:
    """Start a new execution.

    Expects a JSON body containing at least `template_id` and
    `description`. Optional fields include `team_config`,
    `budget_usd` and `custom_requirements`. The orchestrator is
    invoked asynchronously so that this endpoint returns quickly.
    In this demo version authentication is not enforced; in a
    production deployment you would restrict this route and
    populate the `user_id` field accordingly.
    """
    template_id = body.get("template_id")
    description = body.get("description")
    if not template_id or not description:
        raise HTTPException(status_code=400, detail="template_id and description are required")

    team_config = body.get("team_config", "compact")
    budget_usd = float(body.get("budget_usd", 10.0))
    custom_requirements = body.get("custom_requirements", "")

    # Create a new execution ID
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"
    data = {
        "template_id": template_id,
        "description": description,
        "team_config": team_config,
        "budget_usd": budget_usd,
        # For the demo we use a hard-coded user identifier
        "user_id": "demo-user",
        "custom_requirements": custom_requirements,
    }

    # Schedule execution asynchronously
    orchestrator = request.app.state.orchestrator  # type: ignore
    asyncio.create_task(orchestrator.start_execution_async(execution_id, data))

    return {"execution_id": execution_id}
