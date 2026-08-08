"""Generated runtime for reviewer."""

from typing import Any

from runtime.provider import generate


class Agent:
    """Validate the final report against evidence, analysis, risks, and acceptance criteria."""

    name = 'reviewer'
    role = 'final reviewer'

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run independently through the generated project's provider client."""
        missing = [key for key in ['executive_report', 'risk_assessment'] if key not in inputs]
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")
        prompt = (
            f"You are the {self.role} agent '{self.name}'.\n"
            f"Purpose: Validate the final report against evidence, analysis, risks, and acceptance criteria.\n"
            f"Requested task inputs: {inputs!r}\n"
            "Return a useful response that satisfies the agent purpose."
        )
        response = generate(prompt)
        return {"status": "completed", "agent": self.name, "provider": response.provider, "model": response.model, "response": response.text}
