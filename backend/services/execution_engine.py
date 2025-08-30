"""
Simplified execution engine using Celery.

In the full specification the execution engine spins up isolated
containers (or Kubernetes Jobs) to run each task.  This prototype
demonstrates how you could orchestrate tasks via Celery and track
their results.  For demonstration purposes the tasks simply return
success without performing any real work.
"""

from __future__ import annotations

from typing import List, Dict

from celery import Celery


celery_app = Celery(
    "autodev",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(task_serializer="json", result_serializer="json")


@celery_app.task(bind=True)
def execute_job(self, job_data: Dict[str, str]) -> Dict[str, str]:
    """Celery task stub that simulates a job execution.

    The real implementation would invoke the crew runner inside an
    isolated environment, then collect artifacts and record token
    usage.  Here we simply return a success result.
    """
    # Simulate some work by returning a static success structure
    return {
        "status": "succeeded",
        "job_id": job_data.get("id", "unknown"),
        "artifacts": [],
    }


def enqueue_jobs(jobs: List[Dict[str, str]], state_machine: WorkflowStateMachine, execution_id: str) -> List[str]:
    """Enqueue jobs and register state transition hooks."""
    task_ids: List[str] = []
    for job in jobs:
        # Register callback for job completion
        def job_completion_callback():
            # This would update state based on job result
            state_machine.transition(ExecutionState.DEVELOPMENT, "code_complete")
            
        state_machine.register_action(ExecutionState.DEVELOPMENT, job_completion_callback)
        
        result = execute_job.apply_async(args=(job,))
        task_ids.append(result.id)
    return task_ids
