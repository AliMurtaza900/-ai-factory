"""Provider-independent end-to-end factory pipeline."""

from collections.abc import Callable
from dataclasses import dataclass

from ..builder.project import AgentProjectBuilder, GeneratedFile
from ..evaluation.models import EvaluationReport, TestCase
from ..evaluation.runner import AgentCallable, EvaluationRunner
from ..improvement.engine import ImprovementCycle, ImprovementEngine
from ..specs.agent_spec import AgentSpec
from .state import LoopStage, LoopState


@dataclass
class PipelineResult:
    spec: AgentSpec
    generated_files: list[GeneratedFile]
    evaluation: EvaluationReport
    improvement: ImprovementCycle | None
    state: LoopState


class FactoryPipeline:
    """Build and evaluate an agent while keeping revision application explicit."""

    def __init__(
        self,
        builder: AgentProjectBuilder | None = None,
        evaluator: EvaluationRunner | None = None,
        improver: ImprovementEngine | None = None,
        max_iterations: int = 3,
    ) -> None:
        self.builder = builder or AgentProjectBuilder()
        self.evaluator = evaluator or EvaluationRunner()
        self.improver = improver or ImprovementEngine()
        self.max_iterations = max_iterations

    def run(
        self,
        spec: AgentSpec,
        agent: AgentCallable,
        cases: list[TestCase],
    ) -> PipelineResult:
        state = LoopState(max_iterations=self.max_iterations)
        generated = self.builder.build(spec)
        state.transition(LoopStage.EVALUATE, "Agent scaffold generated")

        evaluation = self.evaluator.run(spec.name, agent, cases)
        improvement: ImprovementCycle | None = None

        if evaluation.passed:
            state.transition(LoopStage.APPROVE, "All evaluation tests passed")
            state.transition(LoopStage.COMPLETE, "Agent approved")
        elif state.can_retry():
            state.next_iteration()
            state.transition(LoopStage.IMPROVE, "Evaluation failed; improvement plan created")
            improvement = self.improver.analyze(evaluation)
            # Revision application is deliberately not automatic yet.
            state.transition(LoopStage.FAILED, "Revision requires an explicit implementation backend")
        else:
            state.transition(LoopStage.FAILED, "Iteration limit reached")

        return PipelineResult(spec, generated, evaluation, improvement, state)
