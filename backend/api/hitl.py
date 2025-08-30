"""
Human-in-the-Loop (HITL) API endpoints.

This router is a placeholder for endpoints that allow humans to review and
approve AI-generated outputs. In this simplified demo version, the router
doesn't implement any review logic but serves to illustrate where such
endpoints would be mounted.
"""

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/hitl", tags=["HITL"])


@router.get("/ping")
async def ping() -> dict[str, str]:
    """Simple ping endpoint to verify the HITL router is reachable."""
    return {"message": "HITL router is active"}