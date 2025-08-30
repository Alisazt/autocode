"""
FastAPI application entry point for the AutoDev demo.

This module initializes the FastAPI app, configures CORS, sets up
dependency injection for services, registers API routers and
defines the WebSocket endpoint. During application startup it
creates a single instance of the LLM service and orchestrator and
stores them on the application state so they can be accessed
within request handlers.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from .api.auth import router as auth_router
from .api.executions import router as executions_router
from .services.llm_service import LLMService, LLMConfig, LLMProvider
from .services.orchestrator import Orchestrator
from .services.websocket_manager import websocket_endpoint


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(title="AutoDev Demo", version="0.1.0")

    # Enable CORS for all origins (adjust for production use)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(auth_router)
    app.include_router(executions_router)

    # Create service instances at startup
    @app.on_event("startup")
    async def startup_event() -> None:
        # Load LLM configuration from environment variables. If no API key is
        # provided the orchestrator will operate in demo mode and skip
        # external requests. You can override provider and model by
        # setting environment variables.
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", None)
        default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        llm_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
        )
        app.state.llm_service = LLMService(llm_config)
        # Create orchestrator
        app.state.orchestrator = Orchestrator(app.state.llm_service)

    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        # Properly close any asynchronous resources
        llm_service: LLMService = app.state.llm_service
        # If the LLM service defines an async close method you could await it here
        if hasattr(llm_service, "__aexit__"):
            # Ignore context manager exit errors in demo
            pass

    # Define WebSocket endpoint
    @app.websocket("/ws/{execution_id}")
    async def websocket_route(websocket: WebSocket, execution_id: str) -> None:
        await websocket_endpoint(websocket, execution_id)

    return app


app = create_app()