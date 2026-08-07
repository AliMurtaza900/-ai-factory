"""Models for turning evaluation failures into bounded improvement work."""

from dataclasses import dataclass, field
from enum import Enum

from ..evaluation.models import EvaluationReport


class ImprovementPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ImprovementTask:
    title: str
    reason: str
    priority: ImprovementPriority
    target: str
    evidence: list[str] = field(default_factory=list)
    proposed_changes: list[str] = field(default_factory=list)


@dataclass
class ImprovementPlan:
    agent_name: str
    tasks: list[ImprovementTask] = field(default_factory=list)
    source_score: float = 0.0

    @property
    def actionable(self) -> bool:
        return bool(self.tasks)


def plan_from_report(report: EvaluationReport) -> ImprovementPlan:
    """Create conservative improvement tasks from failed evaluation results."""
    tasks: list[ImprovementTask] = []
    for result in report.results:
        if result.passed:
            continue
        tasks.append(
            ImprovementTask(
                title=f"Fix failing test: {result.test_name}",
                reason=result.message or "Evaluation failure",
                priority=ImprovementPriority.HIGH,
                target="agent implementation",
                evidence=[
                    f"actual={result.actual!r}",
                    f"expected={result.expected!r}",
                ],
                proposed_changes=[
                    "Inspect the failing behavior against the AgentSpec",
                    "Make the smallest change that addresses the observed failure",
                    "Re-run the failed test and the complete regression suite",
                ],
            )
        )
    return ImprovementPlan(
        agent_name=report.agent_name,
        tasks=tasks,
        source_score=report.score,
    )
