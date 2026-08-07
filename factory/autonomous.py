"""Bounded autonomous create -> evaluate -> improve orchestration."""

from dataclasses import dataclass

from .agents.factory_agent import FactoryAgent, FactoryDesign
from .evaluation.factory_evaluator import FactoryEvaluator
from .evaluation.models import EvaluationReport
from .improvement.engine import ImprovementEngine, ImprovementCycle


@dataclass
class AutonomousResult:
    design: FactoryDesign
    report: EvaluationReport
    improvement: ImprovementCycle | None
    attempts: int

    @property
    def passed(self) -> bool:
        return self.report.passed


class AutonomousFactory:
    """Create and validate an agent with a bounded improvement-analysis loop.

    The loop never mutates repository files automatically. Failed evaluations
    produce explicit improvement tasks; a later revision backend can apply them.
    """

    def __init__(self, factory: FactoryAgent | None = None, evaluator: FactoryEvaluator | None = None) -> None:
        self.factory = factory or FactoryAgent()
        self.evaluator = evaluator or FactoryEvaluator()

    def run(self, goal: str, *, max_attempts: int = 2) -> AutonomousResult:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

        design = self.factory.design_and_scaffold(goal)
        report = self.evaluator.evaluate(design.spec, design.files)
        improvement = None
        attempts = 1

        while not report.passed and attempts < max_attempts:
            improvement = ImprovementEngine().analyze(report)
            # Do not silently rewrite artifacts. Revision proposals are explicit
            # and bounded until a revision backend is authorized to apply them.
            break

        if not report.passed and improvement is None:
            improvement = ImprovementEngine().analyze(report)

        return AutonomousResult(
            design=design,
            report=report,
            improvement=improvement,
            attempts=attempts,
        )
