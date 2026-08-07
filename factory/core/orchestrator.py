"""Minimal orchestration engine for the AI Factory.

The orchestrator intentionally starts deterministic and dependency-free. Model
providers, code-generation backends, test runners, and deployment providers can
be plugged in behind the interfaces introduced here.
"""

from collections.abc import Callable

from .models import FactoryJob, JobStatus, PlanStep


Planner = Callable[[FactoryJob], list[PlanStep]]


class FactoryOrchestrator:
    """Coordinate the factory lifecycle without coupling it to one AI provider."""

    def __init__(self, planner: Planner) -> None:
        self.planner = planner

    def run(self, job: FactoryJob) -> FactoryJob:
        """Create a plan and advance the job to the build-ready state."""
        try:
            job.status = JobStatus.PLANNING
            plan = self.planner(job)
            job.metadata["plan"] = [step.__dict__ for step in plan]
            job.status = JobStatus.BUILDING
            return job
        except Exception as exc:  # pragma: no cover - defensive boundary
            job.status = JobStatus.FAILED
            job.errors.append(str(exc))
            return job
