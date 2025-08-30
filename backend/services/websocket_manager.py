"""
WebSocket connection manager for real-time updates in AutoDev.

This module manages WebSocket connections for live execution monitoring,
HITL notifications, and real-time progress updates. It provides a
standard event format and helper methods to broadcast messages to
subscribers.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Dict, List, Set, Optional, Any

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class EventType(str, Enum):
    """Types of events that can be sent via WebSocket."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    HITL_CHECKPOINT_CREATED = "hitl_checkpoint_created"
    HITL_CHECKPOINT_RESOLVED = "hitl_checkpoint_resolved"
    ARTIFACT_GENERATED = "artifact_generated"
    BUDGET_WARNING = "budget_warning"
    ERROR_OCCURRED = "error_occurred"
    LOG_MESSAGE = "log_message"


class WebSocketMessage(BaseModel):
    """Standard WebSocket message format."""
    event_type: EventType
    execution_id: str
    timestamp: str
    data: Dict[str, Any]
    message: Optional[str] = None


class ConnectionManager:
    """Manage WebSocket connections and broadcasting."""

    def __init__(self) -> None:
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.execution_mapping: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, execution_id: str) -> None:
        """Accept a new WebSocket connection and register it."""
        await websocket.accept()
        if execution_id not in self.connections:
            self.connections[execution_id] = set()
        self.connections[execution_id].add(websocket)
        self.execution_mapping[websocket] = execution_id
        await self._send_to_websocket(
            websocket,
            WebSocketMessage(
                event_type=EventType.LOG_MESSAGE,
                execution_id=execution_id,
                timestamp=datetime.utcnow().isoformat(),
                data={},
                message=f"Connected to execution {execution_id}",
            ),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.execution_mapping:
            execution_id = self.execution_mapping[websocket]
            if execution_id in self.connections:
                self.connections[execution_id].discard(websocket)
                if not self.connections[execution_id]:
                    del self.connections[execution_id]
            del self.execution_mapping[websocket]

    async def _send_to_websocket(self, websocket: WebSocket, message: WebSocketMessage) -> None:
        """Send a message to a single WebSocket client."""
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception:
            self.disconnect(websocket)

    async def broadcast_to_execution(self, execution_id: str, message: WebSocketMessage) -> None:
        """Broadcast a message to all clients subscribed to an execution."""
        if execution_id not in self.connections:
            return
        # Copy the set to avoid modification during iteration
        connections = list(self.connections[execution_id])
        for ws in connections:
            await self._send_to_websocket(ws, message)

    async def send_execution_started(self, execution_id: str, template_id: str, team_config: str) -> None:
        message = WebSocketMessage(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"template_id": template_id, "team_config": team_config, "status": "planning"},
            message=f"Execution started with template {template_id}",
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_agent_status(
        self,
        execution_id: str,
        agent: str,
        status: str,
        current_task: Optional[str] = None,
        progress: Optional[float] = None,
    ) -> None:
        message = WebSocketMessage(
            event_type=EventType.AGENT_STATUS_CHANGED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"agent": agent, "status": status, "current_task": current_task, "progress": progress},
            message=f"Agent {agent} is now {status}",
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_execution_progress(
        self,
        execution_id: str,
        overall_progress: float,
        current_phase: str,
        metrics: Dict[str, Any],
    ) -> None:
        message = WebSocketMessage(
            event_type=EventType.EXECUTION_PROGRESS,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"overall_progress": overall_progress, "current_phase": current_phase, "metrics": metrics},
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_hitl_checkpoint(
        self,
        execution_id: str,
        checkpoint_id: str,
        checkpoint_type: str,
        artifacts: List[str],
        message_text: str,
    ) -> None:
        message = WebSocketMessage(
            event_type=EventType.HITL_CHECKPOINT_CREATED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"checkpoint_id": checkpoint_id, "type": checkpoint_type, "artifacts": artifacts, "review_required": True},
            message=message_text,
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_artifact_generated(
        self,
        execution_id: str,
        artifact_path: str,
        agent: str,
        validation_status: bool,
    ) -> None:
        message = WebSocketMessage(
            event_type=EventType.ARTIFACT_GENERATED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"artifact_path": artifact_path, "generated_by": agent, "validated": validation_status},
            message=f"Generated {artifact_path}",
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_budget_warning(
        self,
        execution_id: str,
        usage_percentage: float,
        remaining_budget: float,
    ) -> None:
        message = WebSocketMessage(
            event_type=EventType.BUDGET_WARNING,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"usage_percentage": usage_percentage, "remaining_budget": remaining_budget},
            message=f"Budget warning: {usage_percentage:.1f}% used",
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_log_message(
        self,
        execution_id: str,
        agent: str,
        log_level: str,
        message_text: str,
    ) -> None:
        message = WebSocketMessage(
            event_type=EventType.LOG_MESSAGE,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"agent": agent, "level": log_level},
            message=message_text,
        )
        await self.broadcast_to_execution(execution_id, message)

    async def send_execution_completed(
        self,
        execution_id: str,
        success: bool,
        artifacts: List[str],
        final_metrics: Dict[str, Any],
    ) -> None:
        event_type = EventType.EXECUTION_COMPLETED if success else EventType.EXECUTION_FAILED
        message = WebSocketMessage(
            event_type=event_type,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"success": success, "artifacts": artifacts, "metrics": final_metrics},
            message="Execution completed successfully" if success else "Execution failed",
        )
        await self.broadcast_to_execution(execution_id, message)


# Instantiate a single connection manager for use across the application
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, execution_id: str) -> None:
    """WebSocket endpoint for real‑time execution monitoring.

    This function registers the client with the global connection manager,
    echoes back "pong" messages in response to "ping" and cleans up on
    disconnect. Other messages are ignored. Errors are logged and the
    connection is removed.
    """
    await connection_manager.connect(websocket, execution_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                client_message = json.loads(data)
                if client_message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                # Ignore malformed JSON messages
                pass
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        connection_manager.disconnect(websocket)
        # Print the error for debugging; in production use proper logging
        print(f"WebSocket error: {e}")


async def notify_execution_event(event_type: EventType, execution_id: str, **kwargs) -> None:
    """Dispatch an event to the connection manager based on its type.

    This helper mirrors the signature used in the full AutoDev system
    but is greatly simplified. It calls the appropriate method on
    the global connection manager depending on the event type. Extend
    this function to support additional events if needed.
    """
    if event_type == EventType.EXECUTION_STARTED:
        await connection_manager.send_execution_started(
            execution_id,
            kwargs.get("template_id", ""),
            kwargs.get("team_config", ""),
        )
    elif event_type == EventType.AGENT_STATUS_CHANGED:
        await connection_manager.send_agent_status(
            execution_id,
            kwargs.get("agent", ""),
            kwargs.get("status", ""),
            kwargs.get("current_task"),
            kwargs.get("progress"),
        )
    elif event_type == EventType.EXECUTION_PROGRESS:
        await connection_manager.send_execution_progress(
            execution_id,
            kwargs.get("overall_progress", 0.0),
            kwargs.get("current_phase", ""),
            kwargs.get("metrics", {}),
        )
    elif event_type == EventType.ARTIFACT_GENERATED:
        await connection_manager.send_artifact_generated(
            execution_id,
            kwargs.get("artifact_path", ""),
            kwargs.get("agent", ""),
            kwargs.get("validated", True),
        )
    elif event_type == EventType.BUDGET_WARNING:
        await connection_manager.send_budget_warning(
            execution_id,
            kwargs.get("usage_percentage", 0.0),
            kwargs.get("remaining_budget", 0.0),
        )
    elif event_type == EventType.LOG_MESSAGE:
        await connection_manager.send_log_message(
            execution_id,
            kwargs.get("agent", ""),
            kwargs.get("level", "info"),
            kwargs.get("message_text", ""),
        )
