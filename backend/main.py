"""
Entry point for the CrewAI AutoDev prototype backend with full integrations.

This module constructs and configures the FastAPI application, including
initializing the LLM service on startup, adding CORS middleware, mounting
routers for authentication, human-in-the-loop review, and execution control,
and exposing a WebSocket endpoint for real-time updates.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .api.hitl import router as hitl_router
from .api.auth import router as auth_router
from .api.executions import router as executions_router
from .services.websocket_manager import websocket_endpoint
from .services.llm_service import LLMService, LLMConfig, LLMProvider

from typing import Any

llm_service: LLMService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and shut down services tied to the app's lifespan."""
    global llm_service
    # Instantiate the LLM service based on environment variables
    llm_config = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        default_model="gpt-4o-mini",
    )
    llm_service = LLMService(llm_config)
    yield
    # Cleanup on shutdown
    if llm_service and getattr(llm_service, "session", None):
        await llm_service.session.close()


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI app."""
    app = FastAPI(
        title="CrewAI AutoDev Prototype",
        description="AI-powered code generation platform",
        version="0.1.0",
        lifespan=lifespan,
    )
    # Enable CORS for local development environments
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Register API routers
    app.include_router(auth_router)
    app.include_router(hitl_router)
    app.include_router(executions_router)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "CrewAI AutoDev Prototype backend is running"}

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        return {
            "status": "healthy",
            "services": {
                "llm": "connected" if llm_service else "disconnected",
            },
        }

    @app.websocket("/ws/{execution_id}")
    async def websocket_route(websocket: WebSocket, execution_id: str) -> None:
        await websocket_endpoint(websocket, execution_id)

    return app


# Create a module-level app instance so `uvicorn backend.main:app` works
app = create_app()