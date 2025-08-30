"""
Pydantic and dataclass models used in the AutoDev project.

This module provides minimal stubs for entities referenced by
other services such as the LLM service and authentication. In a
full implementation, these classes would include more fields and
behaviour, and likely interact with a database.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class JobAttempt:
    """A record of a single attempt to run a job via an agent.

    For the purposes of this demo, the fields are minimal.
    """

    attempt_num: int
    status: str
    error: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Artifact:
    """Placeholder Artifact model.

    In a complete system this would include information about the
    file path, version, validation status, and relationships to
    executions or checkpoints. For now it is an empty placeholder.
    """

    id: str
    path: str
    version: int
    content_type: str
    validated: bool = False
    created_by: str = ""
    created_at: Optional[datetime] = None
    execution_id: Optional[str] = None
