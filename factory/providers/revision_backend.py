"""Model-backed revision proposal backend."""

from dataclasses import dataclass

from .base import ModelProvider
from ..improvement.models import ImprovementPlan


@dataclass
class LLMRevisionBackend:
    provider: ModelProvider

    def revise(self, plan: ImprovementPlan) -> list[str]:
        prompt = "\n".join([
            f"Agent: {plan.agent_name}",
            f"Current score: {plan.source_score:.2f}",
            "Failures:",
            *[f"- {task.title}: {task.reason}" for task in plan.tasks],
            "Return a concise list of proposed implementation changes. Do not claim to have modified files.",
        ])
        response = self.provider.generate(prompt)
        return [line.strip(" -") for line in response.text.splitlines() if line.strip()]
