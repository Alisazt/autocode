"""
Entry point for the CrewAI AutoDev prototype backend.

This FastAPI application exposes a minimal set of endpoints to
demonstrate the HITL review workflow and to serve as a foundation
for further development.  Additional routers can be included as the
project evolves.
"""

from fastapi import FastAPI
from .api.hitl import router as hitl_router
from .services.orchestrator import Orchestrator


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    app = FastAPI(title="CrewAI AutoDev Prototype")
    app.include_router(hitl_router)
    
    orchestrator = Orchestrator()

    @app.get("/")
    async def root() -> dict[str, str]:
        """Simple health check endpoint."""
        return {"message": "CrewAI AutoDev Prototype backend is running"}
        
    @app.post("/start")
    async def start_execution():
        """Start a new execution workflow."""
        # In real implementation would get jobs from request
        jobs = [{"id": "job1", "budget": 10.0}]
        orchestrator.start_execution("exec1", jobs)
        return {"status": "execution started"}

    return app


# When run via `uvicorn backend.main:app`, this variable will be used.
app = create_app()
