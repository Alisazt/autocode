"""
Human‑in‑the‑loop (HITL) review endpoints.

These endpoints allow clients to approve or reject checkpoints during
an execution and to fetch the artifacts associated with a checkpoint.
In this prototype the business logic is deliberately minimal – in a
full implementation you would integrate with the state machine,
execution engine and artifact storage.
"""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/hitl", tags=["HITL"])


class HITLApproval(BaseModel):
    """Payload for reviewing a HITL checkpoint."""

    checkpoint_id: str
    action: Literal["approve", "reject"]
    reason: Optional[str] = None
    reviewer_id: str


class HITLResponse(BaseModel):
    """Response returned after a checkpoint review."""

    checkpoint_id: str
    status: str
    next_action: str
    eta_minutes: Optional[int] = None


@router.post("/{checkpoint_id}/review", response_model=HITLResponse)
async def review_checkpoint(checkpoint_id: str, approval: HITLApproval) -> HITLResponse:
    """Approve or reject a checkpoint.

    In this prototype the checkpoint logic is stubbed out.  Approval
    returns a status of `approved` and rejection returns `rejected`.
    When rejecting a checkpoint, a reason must be provided.
    """
    if approval.action == "approve":
        return HITLResponse(
            checkpoint_id=checkpoint_id,
            status="approved",
            next_action="Resuming execution…",
            eta_minutes=15,
        )
    elif approval.action == "reject":
        if not approval.reason:
            raise HTTPException(400, "Reason required for rejection")
        return HITLResponse(
            checkpoint_id=checkpoint_id,
            status="rejected",
            next_action=f"Reworking: {approval.reason}",
            eta_minutes=30,
        )
    else:
        raise HTTPException(400, "Invalid action")


@router.get("/{checkpoint_id}/artifacts")
async def get_checkpoint_artifacts(checkpoint_id: str) -> dict:
    """Fetch artifacts associated with a checkpoint.

    A full implementation would retrieve the artifact list from
    persistent storage and optionally compute diffs between versions.
    Here we return a stubbed list for demonstration purposes.
    """
    # TODO: integrate with artifact storage
    artifacts = [
        {
            "path": "docs/architecture.md",
            "content": "# Architecture\n\nThis is a stubbed artifact.",
            "diff": None,
            "validation_status": True,
        }
    ]
    return {"artifacts": artifacts}
