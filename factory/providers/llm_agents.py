"""Model-backed Architect and Improver adapters."""

import json

from ..evaluation.models import EvaluationReport
from ..improvement.models import ImprovementPlan
from ..specs.agent_spec import AgentSpec
from .base import ModelProvider
from ..agents.prompts import ARCHITECT_SYSTEM_PROMPT, IMPROVER_SYSTEM_PROMPT


class LLMArchitect:
    """Use a model to draft an AgentSpec, with strict JSON parsing."""

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def design(self, goal: str) -> AgentSpec:
        prompt = (
            "Return ONLY valid JSON matching AgentSpec fields. Do not include markdown.\n"
            f"Goal: {goal}"
        )
        response = self.provider.generate(prompt, system=ARCHITECT_SYSTEM_PROMPT)
        try:
            spec = AgentSpec(**json.loads(response.text))
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("Architect model returned invalid AgentSpec JSON") from exc
        errors = spec.validate()
        if errors:
            raise ValueError("Architect produced invalid AgentSpec: " + "; ".join(errors))
        return spec


class LLMImprover:
    """Use a model to propose changes from evaluation evidence."""

    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def propose(self, spec: AgentSpec, report: EvaluationReport) -> ImprovementPlan:
        prompt = json.dumps(
            {
                "task": "Propose the smallest safe improvements.",
                "agent_spec": spec.to_dict(),
                "evaluation": {
                    "passed": report.passed,
                    "score": report.score,
                    "results": [r.__dict__ for r in report.results],
                },
            },
            default=lambda value: getattr(value, "value", str(value)),
        )
        response = self.provider.generate(prompt, system=IMPROVER_SYSTEM_PROMPT)
        # The model output is retained as evidence for a later explicit revision
        # backend rather than being applied directly to files.
        plan = ImprovementPlan(agent_name=spec.name, source_score=report.score)
        plan.tasks.append(
            __import__("factory.improvement.models", fromlist=["ImprovementTask"]).ImprovementTask(
                title="Model-proposed revision",
                reason="Generated from evaluation evidence",
                priority=__import__("factory.improvement.models", fromlist=["ImprovementPriority"]).ImprovementPriority.MEDIUM,
                target="agent implementation",
                evidence=[response.text],
                proposed_changes=[response.text],
            )
        )
        return plan
