"""
Workflow state machine for CrewAI AutoDev.

This module defines a simple state machine for managing the lifecycle
of an execution.  Only a subset of the full specification is
implemented in this prototype.  Additional transitions and states
should be added as needed.
"""

from enum import Enum
from typing import Callable, Dict, Optional


class ExecutionState(Enum):
    """Possible states for an execution."""

    QUEUED = "queued"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    ARCHITECTURE_REVIEW = "architecture_review"
    DEVELOPMENT = "development"
    TESTING = "testing"
    RELEASE_REVIEW = "release_review"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStateMachine:
    """State machine to manage execution transitions with action hooks."""

    def __init__(self) -> None:
        self.transitions: Dict[ExecutionState, Dict[str, ExecutionState]] = {
            ExecutionState.QUEUED: {"auto": ExecutionState.PLANNING},
            ExecutionState.PLANNING: {"planning_complete": ExecutionState.ARCHITECTURE},
            ExecutionState.ARCHITECTURE: {"artifacts_ready": ExecutionState.ARCHITECTURE_REVIEW},
            ExecutionState.ARCHITECTURE_REVIEW: {
                "hitl_approved": ExecutionState.DEVELOPMENT,
                "hitl_rejected": ExecutionState.ARCHITECTURE,
            },
            ExecutionState.DEVELOPMENT: {"code_complete": ExecutionState.TESTING},
            ExecutionState.TESTING: {"tests_passed": ExecutionState.RELEASE_REVIEW},
            ExecutionState.RELEASE_REVIEW: {
                "hitl_approved": ExecutionState.DEPLOYING,
                "hitl_rejected": ExecutionState.TESTING,
            },
            ExecutionState.DEPLOYING: {
                "deploy_success": ExecutionState.COMPLETED,
                "deploy_failed": ExecutionState.FAILED,
            },
        }
        # Action hooks for state transitions
        self.action_hooks: Dict[ExecutionState, Callable] = {}

    def can_transition(self, current: ExecutionState, event: str) -> bool:
        return event in self.transitions.get(current, {})

    def next_state(self, current: ExecutionState, event: str) -> Optional[ExecutionState]:
        return self.transitions.get(current, {}).get(event)

    def register_action(self, state: ExecutionState, action: Callable):
        """Register an action to be executed when entering a state."""
        self.action_hooks[state] = action

    def transition(self, current: ExecutionState, event: str) -> Optional[ExecutionState]:
        """Perform state transition and execute associated action."""
        next_state = self.next_state(current, event)
        if next_state and next_state in self.action_hooks:
            self.action_hooks[next_state]()
        return next_state
