"""Generated runtime for researcher."""

from typing import Any

from runtime.provider import generate


class Agent:
    """Research the business question using multiple relevant sources."""

    name = 'researcher'
    role = 'research'

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run independently through the generated project's provider client."""
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")
        missing = [key for key in ['business_question'] if key not in inputs]
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")
        prompt = (
            f"You are the {self.role} agent '{self.name}'.\n"
            f"Purpose: Research the business question using multiple relevant sources.\n"
            f"Requested task inputs: {inputs!r}\n"
            "Return a useful response that satisfies the agent purpose."
        )
        response = generate(prompt)
        if not response.text.strip():
            raise RuntimeError("provider returned an empty response")
        return {"status": "completed", "agent": self.name, "provider": response.provider, "model": response.model, "response": response.text}
