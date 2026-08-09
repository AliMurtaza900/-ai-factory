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

    @staticmethod
    def _parse_json_object(text: str) -> dict:
        """Extract the first valid JSON object from a model response.

        Models sometimes wrap otherwise-valid JSON in markdown fences or a short
        explanatory sentence. The architect contract is JSON, so tolerate those
        harmless wrappers while still rejecting empty or malformed responses.
        """
        raw = (text or "").strip()
        if not raw:
            raise ValueError("LLM architect returned an empty response")

        candidates = [raw]
        fenced = re.findall(r"```(?:json)?\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL)
        candidates.extend(block.strip() for block in fenced if block.strip())

        for candidate in candidates:
            try:
                value = json.loads(candidate)
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                pass

        start = raw.find("{")
        while start >= 0:
            depth = 0
            in_string = False
            escaped = False
            for index in range(start, len(raw)):
                char = raw[index]
                if in_string:
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif char == '"':
                        in_string = False
                    continue
                if char == '"':
                    in_string = True
                elif char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            value = json.loads(raw[start:index + 1])
                            if isinstance(value, dict):
                                return value
                        except json.JSONDecodeError:
                            break
            start = raw.find("{", start + 1)

        raise ValueError("LLM architect response was not a valid JSON object")

    def _llm_design(self, goal: str) -> AgentSpec:
        provider = self.provider or configured_provider()
        prompt = f"""Design an AI agent for this goal: {goal}
Return ONLY valid JSON with these keys: name, purpose, role, inputs, outputs, capabilities, constraints, acceptance_criteria.
Each list value must be an array of strings. Do not include markdown or commentary."""
        response = provider.generate(
            prompt,
            system="You are an AI systems architect. Return only the requested JSON object.",
        )
        data = self._parse_json_object(response.text)
        required = ["name", "purpose", "role", "inputs", "outputs", "capabilities", "constraints", "acceptance_criteria"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"LLM architect response is missing required fields: {', '.join(missing)}")
        list_fields = ["inputs", "outputs", "capabilities", "constraints", "acceptance_criteria"]
        if any(not isinstance(data[key], list) for key in list_fields):
            raise ValueError("LLM architect list fields must be arrays")
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
