"""Minimal orchestration engine for the AI Factory.

The orchestrator intentionally starts deterministic and dependency-free. Model
providers, code-generation backends, test runners, and deployment providers can
be plugged in behind the interfaces introduced here.
"""

from collections.abc import Callable, Iterable

from .models import FactoryJob, JobStatus, PlanStep


Planner = Callable[[FactoryJob], list[PlanStep]]
ArtifactCollector = Callable[[FactoryJob], Iterable[str]]


class FactoryOrchestrator:
    """Coordinate the factory lifecycle without coupling it to one AI provider."""

    def __init__(self, planner: Planner, artifact_collector: ArtifactCollector | None = None) -> None:
        self.planner = planner
        self.artifact_collector = artifact_collector

    def run(self, job: FactoryJob) -> FactoryJob:
        """Create a plan, record produced artifacts, and advance the job."""
        try:
            job.status = JobStatus.PLANNING
            plan = self.planner(job)
            job.metadata["plan"] = [step.__dict__ for step in plan]
            job.status = JobStatus.BUILDING

            if self.artifact_collector is not None:
                for artifact in self.artifact_collector(job):
                    value = str(artifact)
                    if value and value not in job.artifacts:
                        job.artifacts.append(value)

            return job
        except Exception as exc:  # pragma: no cover - defensive boundary
            job.status = JobStatus.FAILED
            job.errors.append(str(exc))
            return job
