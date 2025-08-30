"""
Pydantic models and enums for the CrewAI AutoDev prototype.

These classes are simplified representations of the data structures
described in the specification.  They can be used for request/response
models and internal state tracking.  As the project matures you may
wish to move some of these into separate modules or introduce a more
robust ORM.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel


class HITLStatus(str, Enum):
    """Possible states for a HITL checkpoint."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    timeout = "timeout"
    rework = "rework"


class JobAttempt(BaseModel):
    """Record of a single attempt to execute a job."""

    attempt_num: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: Literal["running", "succeeded", "failed"]
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    artifacts: Optional[List[str]] = None


class ExecutionJob(BaseModel):
    """Job definition for the execution engine."""

    id: str
    execution_id: str
    task_id: str
    agent: str
    status: Literal["queued", "running", "succeeded", "failed", "retrying"]
    idempotency_key: str
    attempts: Optional[List[JobAttempt]] = None
    timeout_sec: Optional[int] = None
    max_retries: Optional[int] = None
    cost_budget_usd: Optional[float] = None
    model: Optional[str] = None


class Artifact(BaseModel):
    """Metadata about a generated artifact."""

    id: str
    project_id: str
    execution_id: str
    path: str
    storage_url: str
    content_type: str
    checksum: str
    version: int
    size: int
    created_by: str
    created_at: str
    validated: Optional[bool] = None
    parent_version: Optional[int] = None


class HITLCheckpoint(BaseModel):
    """A checkpoint requiring human review."""

    id: str
    execution_id: str
    type: Literal["architecture_review", "code_review", "release_approval"]
    status: HITLStatus
    artifacts: List[str] = []
    reviewer: Optional[str] = None
    reason: Optional[str] = None
    due_at: str
    approved_at: Optional[str] = None
