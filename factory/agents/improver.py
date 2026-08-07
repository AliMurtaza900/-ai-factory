"""Improver role wrapping evidence-based improvement planning."""

from ..evaluation.models import EvaluationReport
from ..improvement.engine import ImprovementCycle, ImprovementEngine


class ImproverAgent:
    role = "improver"

    def __init__(self, engine: ImprovementEngine | None = None) -> None:
        self.engine = engine or ImprovementEngine()

    def analyze(self, report: EvaluationReport) -> ImprovementCycle:
        return self.engine.analyze(report)
