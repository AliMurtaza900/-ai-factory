"""Safe, bounded application of improvement proposals to generated projects."""

from dataclasses import dataclass
from typing import Callable

from ..builder.project import GeneratedFile
from ..evaluation.factory_evaluator import FactoryEvaluator
from ..evaluation.models import EvaluationReport
from ..specs.agent_spec import AgentSpec


@dataclass(frozen=True)
class ImprovementResult:
    files: list[GeneratedFile]
    report: EvaluationReport
    iterations: int
    changed: bool


class ImprovementApplier:
    """Apply only explicitly supported, bounded changes and re-evaluate each iteration."""

    def __init__(self, evaluator: FactoryEvaluator | None = None, max_iterations: int = 2):
        self.evaluator = evaluator or FactoryEvaluator()
        self.max_iterations = max(0, max_iterations)

    def improve(
        self,
        spec: AgentSpec,
        files: list[GeneratedFile],
        proposal_applier: Callable[[list[GeneratedFile], list[str]], list[GeneratedFile]] | None = None,
    ) -> ImprovementResult:
        current = list(files)
        report = self.evaluator.evaluate(spec, current)
        iterations = 0
        changed = False

        while not report.passed and iterations < self.max_iterations:
            if proposal_applier is None:
                break
            proposals = [r.message for r in report.results if not r.passed]
            updated = proposal_applier(current, proposals)
            if updated == current:
                break
            current = updated
            changed = True
            iterations += 1
            report = self.evaluator.evaluate(spec, current)

        return ImprovementResult(current, report, iterations, changed)
