"""
Simple budget and cost tracking for demo purposes.

This module provides a minimal `CostTracker` class that tracks
token usage and cost against a budget. It is a placeholder for
the more sophisticated budget manager in the full AutoDev system.
"""

from typing import Dict


class CostTracker:
    """Track usage of tokens and cost against a budget.

    Attributes:
        budget_usd: The maximum budget allowed for the task.
        tokens_used: Cumulative number of tokens used.
        cost_usd: Total cost incurred so far.
    """

    def __init__(self, budget_usd: float = 1.0):
        self.budget_usd = float(budget_usd)
        self.tokens_used: int = 0
        self.cost_usd: float = 0.0

    def add_usage(self, input_tokens: int, output_tokens: int) -> bool:
        """Add token usage and update cost.

        Returns True if the budget has been exceeded.
        """
        self.tokens_used += input_tokens + output_tokens
        # simplistic pricing: 0.0005 USD per 1000 tokens
        self.cost_usd += (input_tokens + output_tokens) / 1000 * 0.0005
        return self.cost_usd >= self.budget_usd

    def remaining_budget(self) -> float:
        """Return remaining budget in USD."""
        return max(0.0, self.budget_usd - self.cost_usd)

    def usage_percentage(self) -> float:
        """Return the percentage of budget used."""
        if self.budget_usd == 0:
            return 100.0
        return (self.cost_usd / self.budget_usd) * 100


class BudgetManager:
    """Manage budgets for multiple tasks within an execution.

    This minimal implementation simply stores a mapping of task IDs
    to `CostTracker` instances. In a production system, it would
    support more complex features such as global budgets, rate limits,
    and persistent storage.
    """

    def __init__(self) -> None:
        self.execution_trackers: Dict[str, Dict[str, CostTracker]] = {}

    def init_execution_budget(self, execution_id: str, task_budgets: Dict[str, float]):
        """Initialize cost trackers for each task in an execution."""
        trackers: Dict[str, CostTracker] = {}
        for task_id, budget in task_budgets.items():
            trackers[task_id] = CostTracker(budget)
        self.execution_trackers[execution_id] = trackers
