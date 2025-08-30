"""
Simplified orchestrator for the AutoDev demo.

This orchestrator coordinates execution of a project template by
combining the LLM service, budget manager, guardrails and
websocket connection manager. It demonstrates how an execution
workflow might be orchestrated without implementing every phase
found in the full AutoDev system. The orchestrator runs
asynchronously to avoid blocking HTTP requests and sends real‑time
updates to connected WebSocket clients.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional, List

from ..services.llm_service import LLMService, CodeGenerationAgent
from ..services.websocket_manager import connection_manager
from ..services.budget_manager import BudgetManager
from ..services.guardrails import GuardrailsEngine


class ExecutionContext:
    """Hold execution state and intermediate data.

    The context stores input parameters, progress, metrics and
    generated artifacts. In a full implementation this would
    persist to a database between events. For the demo we keep
    everything in memory.
    """
    def __init__(self, execution_id: str, data: Dict[str, Any]):
        self.execution_id = execution_id
        self.template_id: str = data.get("template_id", "")
        self.description: str = data.get("description", "")
        self.team_config: str = data.get("team_config", "compact")
        self.budget_usd: float = float(data.get("budget_usd", 10.0))
        self.user_id: str = data.get("user_id", "")
        self.custom_requirements: str = data.get("custom_requirements", "")

        # Execution progress and phase tracking
        self.current_phase: str = "queued"
        self.progress: float = 0.0
        self.metrics: Dict[str, Any] = {"tokens_used": 0, "cost_usd": 0.0, "duration": 0.0}
        # Generated artifacts keyed by logical path
        self.artifacts: Dict[str, Any] = {}
        # Flag to indicate if execution has encountered an error
        self.error: Optional[str] = None


class Orchestrator:
    """Coordinate execution of an AutoDev project.

    The orchestrator drives the workflow for a single execution. It
    maintains an in‑memory mapping of execution IDs to contexts and
    uses the LLM service to generate architecture artefacts. After
    each phase it sends status updates via the WebSocket connection
    manager. This class is a drastically simplified version of the
    orchestrator found in the full AutoDev implementation.
    """

    def __init__(self, llm_service: LLMService) -> None:
        self.llm_service = llm_service
        self.code_agent = CodeGenerationAgent(llm_service)
        self.budget_manager = BudgetManager()
        self.guardrails = GuardrailsEngine()
        # In‑memory storage for execution contexts
        self.executions: Dict[str, ExecutionContext] = {}

    async def start_execution_async(self, execution_id: str, data: Dict[str, Any]) -> None:
        """Entry point to start an execution asynchronously.

        Creates a context, initializes budgets, notifies clients and
        schedules the workflow tasks. Errors are caught and
        propagated via WebSocket messages.
        """
        context = ExecutionContext(execution_id, data)
        self.executions[execution_id] = context

        # Initialize budget; we use a single task 'main' for demo
        self.budget_manager.init_execution_budget(execution_id, {"main": context.budget_usd})

        # Notify clients that execution has started
        await connection_manager.send_execution_started(
            execution_id, context.template_id, context.team_config
        )

        try:
            # Kick off planning and architecture sequentially
            await self._handle_planning(context)
            await self._handle_architecture(context)

            # Mark execution complete
            await connection_manager.send_execution_progress(
                execution_id,
                1.0,
                "completed",
                context.metrics,
            )
            await connection_manager.send_log_message(
                execution_id, "orchestrator", "info", "Execution completed successfully"
            )

        except Exception as e:
            context.error = str(e)
            await connection_manager.send_log_message(
                execution_id, "orchestrator", "error", f"Execution failed: {str(e)}"
            )

    async def _handle_planning(self, context: ExecutionContext) -> None:
        """Simulate the planning phase.

        Updates progress and sends a status event. In this demo we
        merely wait for a brief period to simulate work.
        """
        context.current_phase = "planning"
        context.progress = 0.1
        await connection_manager.send_execution_progress(
            context.execution_id,
            context.progress,
            context.current_phase,
            context.metrics,
        )
        await connection_manager.send_agent_status(
            context.execution_id, "planner", "working", current_task="planning", progress=context.progress
        )
        # Simulate some planning time
        await asyncio.sleep(1)
        context.progress = 0.2
        await connection_manager.send_execution_progress(
            context.execution_id,
            context.progress,
            context.current_phase,
            context.metrics,
        )
        await connection_manager.send_agent_status(
            context.execution_id, "planner", "completed", current_task="planning", progress=context.progress
        )

    async def _handle_architecture(self, context: ExecutionContext) -> None:
        """Generate the project architecture via the LLM service.

        Uses the code generation agent to build a project skeleton. A
        cost tracker is obtained from the budget manager to limit
        spending. Generated files are stored in the execution context
        and broadcast to connected clients. If the budget is
        exhausted a warning is emitted but execution continues.
        """
        context.current_phase = "architecture"
        context.progress = 0.3
        await connection_manager.send_execution_progress(
            context.execution_id,
            context.progress,
            context.current_phase,
            context.metrics,
        )
        await connection_manager.send_agent_status(
            context.execution_id, "architect", "working", current_task="architecture", progress=context.progress
        )

        # Acquire cost tracker for this execution
        cost_tracker = self.budget_manager.execution_trackers[context.execution_id]["main"]

        import os
        from pathlib import Path

        llm_mode = os.getenv("LLM_MODE", "demo").lower()
        project_data: Dict[str, Any] = {}
        budget_exceeded = False

        if llm_mode != "demo":
            # Generate project structure via LLM
            async with self.llm_service:
                project_data, budget_exceeded = await self.code_agent.generate_project_structure(
                    context.template_id,
                    f"{context.description}\n\nAdditional requirements: {context.custom_requirements}",
                    cost_tracker,
                )
        else:
            # Demo mode: load static templates from the templates directory
            template_dir = Path(__file__).resolve().parents[2] / "templates" / context.template_id
            files: Dict[str, str] = {}
            # Read architecture markdown
            arch_path = template_dir / "architecture.md"
            if arch_path.exists():
                files["docs/architecture.md"] = arch_path.read_text(encoding="utf-8")
            # Read OpenAPI spec
            api_path = template_dir / "openapi.yaml"
            if api_path.exists():
                files["docs/api.yaml"] = api_path.read_text(encoding="utf-8")
            project_data = {"files": files, "architecture": {}, "structure": [], "instructions": "Demo project"}

        # Update metrics after generation
        context.metrics["tokens_used"] = cost_tracker.tokens_used
        context.metrics["cost_usd"] = cost_tracker.cost_usd

        # Emit budget warning if necessary
        if cost_tracker.usage_percentage() > 80:
            await connection_manager.send_budget_warning(
                context.execution_id,
                cost_tracker.usage_percentage(),
                cost_tracker.remaining_budget(),
            )

        # Store generated files in context.artifacts and notify clients
        files = project_data.get("files", {}) if project_data else {}
        for path, content in files.items():
            context.artifacts[path] = content
            await connection_manager.send_artifact_generated(
                context.execution_id, path, "architect", True
            )

        # Validate architecture (stubbed)
        if project_data and "architecture" in project_data:
            is_valid, errors = self.guardrails.validate_artifact("architecture", project_data["architecture"])
            if not is_valid:
                await connection_manager.send_log_message(
                    context.execution_id,
                    "architect",
                    "warning",
                    f"Architecture validation failed: {', '.join(errors)}",
                )

        # Advance progress and mark architecture complete
        context.progress = 0.6
        await connection_manager.send_execution_progress(
            context.execution_id,
            context.progress,
            context.current_phase,
            context.metrics,
        )
        await connection_manager.send_agent_status(
            context.execution_id, "architect", "completed", current_task="architecture", progress=context.progress
        )
