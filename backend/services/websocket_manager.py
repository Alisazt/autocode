"""
WebSocket connection manager for real-time updates.

This module defines a simple connection manager that tracks WebSocket clients
subscribed to a particular execution and provides helper methods to send
structured events to those clients. It also exposes a `websocket_endpoint`
function that can be mounted on the FastAPI app.
"""

from __future__ import annotations
import json
from typing import Dict, Set, Any
from datetime import datetime
from enum import Enum
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel


class EventType(str, Enum):
    """Enumeration of possible event types sent over the WebSocket."""
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETED = "execution_completed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    HITL_CHECKPOINT_CREATED = "hitl_checkpoint_created"
    ARTIFACT_GENERATED = "artifact_generated"
    LOG_MESSAGE = "log_message"


class WebSocketMessage(BaseModel):
    """Data model for messages sent to clients over WebSocket."""
    event_type: EventType
    execution_id: str
    timestamp: str
    data: Dict[str, Any]
    message: str = ""


class ConnectionManager:
    """
    Manages active WebSocket connections keyed by execution id. Allows broadcasting
    messages to all clients subscribed to a particular execution.
    """
    def __init__(self) -> None:
        self.connections: Dict[str, Set[WebSocket]] = {}
        self.execution_mapping: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, execution_id: str) -> None:
        """Accept a WebSocket connection and register it under the given execution id."""
        await websocket.accept()
        if execution_id not in self.connections:
            self.connections[execution_id] = set()
        self.connections[execution_id].add(websocket)
        self.execution_mapping[websocket] = execution_id
        # Notify the client that it is connected
        await self._send_to_websocket(websocket, WebSocketMessage(
            event_type=EventType.LOG_MESSAGE,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={},
            message=f"Connected to execution {execution_id}"
        ))

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket from the connection lists when disconnected."""
        if websocket in self.execution_mapping:
            execution_id = self.execution_mapping[websocket]
            if execution_id in self.connections:
                self.connections[execution_id].discard(websocket)
                if not self.connections[execution_id]:
                    del self.connections[execution_id]
            del self.execution_mapping[websocket]

    async def _send_to_websocket(self, websocket: WebSocket, message: WebSocketMessage) -> None:
        """Send a single message to a specific WebSocket client."""
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception:
            # Disconnect on error
            self.disconnect(websocket)

    async def broadcast_to_execution(self, execution_id: str, message: WebSocketMessage) -> None:
        """Send a message to all clients subscribed to a given execution id."""
        if execution_id not in self.connections:
            return
        for websocket in list(self.connections[execution_id]):
            await self._send_to_websocket(websocket, message)

    async def send_execution_started(self, execution_id: str, template_id: str, team_config: str) -> None:
        """Broadcast that an execution has started."""
        msg = WebSocketMessage(
            event_type=EventType.EXECUTION_STARTED,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"template_id": template_id, "team_config": team_config, "status": "planning"},
            message=f"Execution started with template {template_id}"
        )
        await self.broadcast_to_execution(execution_id, msg)

    async def send_progress_update(self, execution_id: str, progress: float, phase: str, metrics: Dict[str, Any]) -> None:
        """Broadcast an execution progress update."""
        msg = WebSocketMessage(
            event_type=EventType.EXECUTION_PROGRESS,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"progress": progress, "phase": phase, "metrics": metrics},
            message=f"Progress: {progress * 100:.1f}% - {phase}"
        )
        await self.broadcast_to_execution(execution_id, msg)

    async def send_log_message(self, execution_id: str, agent: str, level: str, message_text: str) -> None:
        """Broadcast a log message from an agent."""
        msg = WebSocketMessage(
            event_type=EventType.LOG_MESSAGE,
            execution_id=execution_id,
            timestamp=datetime.utcnow().isoformat(),
            data={"agent": agent, "level": level},
            message=message_text
        )
        await self.broadcast_to_execution(execution_id, msg)


# A global instance of the connection manager that can be imported and used
connection_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, execution_id: str) -> None:
    """
    FastAPI websocket endpoint handler. Accepts connections, listens for client
    pings and disconnects gracefully.
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
                # Ignore malformed messages
                pass
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)