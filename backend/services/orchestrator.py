from __future__ import annotations
from typing import Dict, Any
from .state_machine import WorkflowStateMachine, ExecutionState
from .execution_engine import enqueue_jobs
from .budget_manager import BudgetManager
from .guardrails import GuardrailsEngine

class Orchestrator:
    """Coordinates workflow execution across services."""
    
    def __init__(self):
        self.state_machine = WorkflowStateMachine()
        self.budget_manager = BudgetManager()
        self.guardrails = GuardrailsEngine()
        self.current_state = ExecutionState.QUEUED
        
    def start_execution(self, execution_id: str, jobs: Dict[str, Any]):
        """Start a new execution workflow."""
        # Initialize budgets for tasks
        task_budgets = {job['id']: job.get('budget', 10.0) for job in jobs}
        self.budget_manager.init_execution_budget(execution_id, task_budgets)
        
        # Register state actions
        self._register_state_actions(execution_id)
        
        # Start from QUEUED state
        self._transition("auto")
        
    def _register_state_actions(self, execution_id: str):
        """Register actions for state transitions."""
        self.state_machine.register_action(ExecutionState.PLANNING, self._planning_action)
        self.state_machine.register_action(ExecutionState.DEVELOPMENT, 
            lambda: enqueue_jobs(execution_id, self.state_machine))
        
    def _transition(self, event: str):
        """Process state transition."""
        next_state = self.state_machine.transition(self.current_state, event)
        if next_state:
            self.current_state = next_state
            
    def _planning_action(self):
        """Example planning phase action."""
        print("Starting planning phase")
        # In real implementation would invoke planning agents
        
    def handle_event(self, event: str):
        """Handle external events (e.g., HITL approvals)."""
        self._transition(event)