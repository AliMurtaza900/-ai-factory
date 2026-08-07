"""Coordinate CI feedback with bounded improvement planning."""

from dataclasses import dataclass

from ..improvement.engine import ImprovementCycle, ImprovementEngine
from ..evaluation.models import EvaluationReport
from .ci import CIResult, ci_result_to_report


@dataclass
class FeedbackDecision:
    report: EvaluationReport
    improvement: ImprovementCycle | None


class FeedbackLoop:
    """Convert a CI result into either approval or a revision plan."""

    def __init__(self, improver: ImprovementEngine | None = None) -> None:
        self.improver = improver or ImprovementEngine()

    def process(self, agent_name: str, ci: CIResult) -> FeedbackDecision:
        report = ci_result_to_report(agent_name, ci)
        if report.passed:
            return FeedbackDecision(report=report, improvement=None)
        return FeedbackDecision(report=report, improvement=self.improver.analyze(report))
