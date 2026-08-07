"""Architect role: turn a natural-language goal into an AgentSpec."""

import json
import os
import re

from ..specs.agent_spec import AgentSpec
from ..providers.factory import configured_provider


class ArchitectAgent:
    """Use the configured provider chain when enabled, with a deterministic fallback."""

    role = "architect"

    def __init__(self, provider=None) -> None:
        self.provider = provider

    @staticmethod
    def _deterministic(goal: str) -> AgentSpec:
        clean = re.sub(r"\s+", " ", goal).strip()
        name = re.sub(r"[^a-z0-9]+", "-", clean.lower()).strip("-")[:48] or "generated-agent"
        return AgentSpec(
            name=name,
            purpose=clean,
            role="general-purpose AI agent",
            inputs=["user_request"],
            outputs=["agent_response"],
            capabilities=["reasoning", "structured response generation"],
            constraints=["follow the specification", "do not fabricate unavailable evidence"],
            acceptance_criteria=[
                "Accepts the declared input",
                "Produces the declared output",
                "Reports uncertainty when required",
            ],
            metadata={"created_by": "architect", "source_goal": clean},
        )

    def _llm_design(self, goal: str) -> AgentSpec:
        provider = self.provider or configured_provider()
        prompt = f"""Design an AI agent for this goal: {goal}
Return ONLY valid JSON with these keys: name, purpose, role, inputs, outputs, capabilities, constraints, acceptance_criteria.
Each list value must be an array of strings. Do not include markdown or commentary."""
        response = provider.generate(
            prompt,
            system="You are an AI systems architect. Return only the requested JSON object.",
        )
        data = json.loads(response.text)
        required = ["name", "purpose", "role", "inputs", "outputs", "capabilities", "constraints", "acceptance_criteria"]
        if any(key not in data for key in required):
            raise ValueError("LLM architect response is missing required fields")
        return AgentSpec(
            name=str(data["name"]),
            purpose=str(data["purpose"]),
            role=str(data["role"]),
            inputs=[str(x) for x in data["inputs"]],
            outputs=[str(x) for x in data["outputs"]],
            capabilities=[str(x) for x in data["capabilities"]],
            constraints=[str(x) for x in data["constraints"]],
            acceptance_criteria=[str(x) for x in data["acceptance_criteria"]],
            metadata={"created_by": self.role, "source_goal": goal, "llm_architect": True, "provider": response.provider, "model": response.model},
        )

    def design(self, goal: str) -> AgentSpec:
        if not goal or not goal.strip():
            raise ValueError("A non-empty goal is required")

        if os.getenv("AI_FACTORY_ENABLE_LLM_ARCHITECT", "0").lower() in {"1", "true", "yes"}:
            try:
                return self._llm_design(goal.strip())
            except Exception as exc:
                print(f"LLM architect unavailable -> deterministic fallback: {exc}")

        return self._deterministic(goal)
