"""Coordinate versioned, bounded revision cycles."""

from dataclasses import dataclass

from ..evaluation.models import EvaluationReport
from ..improvement.engine import ImprovementEngine, ImprovementCycle
from ..registry.store import RegistryStore


@dataclass
class RevisionCycleResult:
    agent_id: str
    version: int | None
    report: EvaluationReport
    improvement: ImprovementCycle | None
    should_retry: bool


class AutonomousRevisionCycle:
    """Record results and request improvements without silently applying code."""

    def __init__(self, registry: RegistryStore | None = None, improver: ImprovementEngine | None = None, max_retries: int = 3) -> None:
        self.registry = registry or RegistryStore()
        self.improver = improver or ImprovementEngine()
        self.max_retries = max_retries

    def process(self, agent_id: str, agent_name: str, spec: dict, files: list[str], report: EvaluationReport) -> RevisionCycleResult:
        approved = report.passed
        version = self.registry.register_version(
            agent_id=agent_id,
            name=agent_name,
            spec=spec,
            files=files,
            score=report.score,
            approved=approved,
            notes=["Approved by evaluation" if approved else "Evaluation failed; revision required"],
        )
        improvement = None if approved else self.improver.analyze(report)
        existing = self.registry.get(agent_id)
        retries = len(existing.versions) - 1 if existing else 0
        return RevisionCycleResult(
            agent_id=agent_id,
            version=version.version,
            report=report,
            improvement=improvement,
            should_retry=not approved and retries < self.max_retries,
        )
