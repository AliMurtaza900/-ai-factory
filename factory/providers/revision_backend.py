"""Model-backed revision proposal backend with tolerant output normalization."""

from dataclasses import dataclass
import json
import re

from .base import ModelProvider
from ..improvement.models import ImprovementPlan


@dataclass
class LLMRevisionBackend:
    provider: ModelProvider

    @staticmethod
    def _normalize(text: str) -> list[str]:
        """Accept JSON, bullets, or plain lines and return clean proposal strings."""
        text = text.strip()
        if not text:
            return []

        # Prefer structured JSON when the model supplies it.
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
            if isinstance(data, dict):
                for key in ("proposals", "changes", "tasks", "items"):
                    value = data.get(key)
                    if isinstance(value, list):
                        return [str(item).strip() for item in value if str(item).strip()]
        except (json.JSONDecodeError, TypeError):
            pass

        proposals: list[str] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            line = re.sub(r"^proposal\s*:\s*", "", line, flags=re.IGNORECASE)
            line = re.sub(r"^(?:[-*+] |\d+[.)]\s*)", "", line)
            line = line.strip()
            if line:
                proposals.append(line)
        return proposals

    def revise(self, plan: ImprovementPlan) -> list[str]:
        prompt = "\n".join([
            f"Agent: {plan.agent_name}",
            f"Current score: {plan.source_score:.2f}",
            "Failures:",
            *[f"- {task.title}: {task.reason}" for task in plan.tasks],
            "Return implementation changes as a JSON array of strings when possible.",
            "If JSON is unavailable, return one concise change per line.",
            "Do not claim to have modified files.",
        ])
        response = self.provider.generate(prompt)
        return self._normalize(response.text)
