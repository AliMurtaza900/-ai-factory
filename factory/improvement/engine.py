"""Bounded improvement loop orchestration."""

from dataclasses import dataclass
from typing import Protocol

from ..evaluation.models import EvaluationReport
from .models import ImprovementPlan, plan_from_report


class RevisionBackend(Protocol):
    """Interface for a model or human-controlled revision backend."""

    def revise(self, plan: ImprovementPlan) -> list[str]:
        """Return proposed change descriptions; do not mutate files directly."""
        ...


@dataclass
class ImprovementCycle:
    plan: ImprovementPlan
    proposed_changes: list[str]


class ImprovementEngine:
    """Analyze failures and request bounded revisions without auto-executing them."""

    def __init__(self, backend: RevisionBackend | None = None) -> None:
        self.backend = backend

    def analyze(self, report: EvaluationReport) -> ImprovementCycle:
        plan = plan_from_report(report)
        proposed = []
        if self.backend is not None and plan.actionable:
            proposed = self.backend.revise(plan)
        return ImprovementCycle(plan=plan, proposed_changes=proposed)
