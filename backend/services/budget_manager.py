"""
Cost management and budget tracking utilities.

This module defines simple classes for tracking the cost and token
usage of a job execution.  The pricing table is derived from the
specification but simplified for this prototype.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class CostTracker:
    """Track token and dollar usage for a single task."""

    budget_usd: float
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = "gpt-4o-mini"

    # Approximate pricing per 1K tokens (input/output)
    MODEL_COSTS: Dict[str, Dict[str, float]] = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.0025, "output": 0.01},
    }

    def add_usage(self, input_tokens: int, output_tokens: int) -> bool:
        """Add token usage and return True if budget is exceeded."""
        costs = self.MODEL_COSTS.get(self.model, self.MODEL_COSTS["gpt-4o-mini"])
        additional = (
            (input_tokens / 1000.0) * costs["input"]
            + (output_tokens / 1000.0) * costs["output"]
        )
        self.tokens_used += input_tokens + output_tokens
        self.cost_usd += additional
        return self.cost_usd >= self.budget_usd

    def remaining_budget(self) -> float:
        return max(0.0, self.budget_usd - self.cost_usd)

    def usage_percentage(self) -> float:
        if self.budget_usd == 0:
            return 0.0
        return (self.cost_usd / self.budget_usd) * 100.0


class BudgetManager:
    """Manage cost trackers for multiple executions and tasks."""

    def __init__(self) -> None:
        self.execution_trackers: Dict[str, Dict[str, CostTracker]] = {}

    def init_execution_budget(self, execution_id: str, task_budgets: Dict[str, float]) -> None:
        """Initialize trackers for each task in an execution."""
        self.execution_trackers[execution_id] = {
            task_id: CostTracker(budget_usd=budget)
            for task_id, budget in task_budgets.items()
        }

    def check_task_budget(
        self,
        execution_id: str,
        task_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Tuple[bool, str]:
        """Record usage and return a tuple (allowed, message)."""
        tracker = self.execution_trackers[execution_id][task_id]
        exceeded = tracker.add_usage(input_tokens, output_tokens)
        if exceeded:
            return False, f"Budget exceeded: ${tracker.cost_usd:.3f} / ${tracker.budget_usd:.2f}"
        if tracker.usage_percentage() > 80:
            return True, f"Budget warning: {tracker.usage_percentage():.1f}% used"
        return True, ""
