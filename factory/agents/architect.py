"""Architect role: turn a natural-language goal into an AgentSpec."""

import re

from ..specs.agent_spec import AgentSpec


class ArchitectAgent:
    """Deterministic baseline architect; an LLM backend can replace its heuristics."""

    role = "architect"

    def design(self, goal: str) -> AgentSpec:
        if not goal or not goal.strip():
            raise ValueError("A non-empty goal is required")

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
            metadata={"created_by": self.role, "source_goal": clean},
        )
