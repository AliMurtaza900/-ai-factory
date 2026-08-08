"""Generated runtime for risk_analyst."""

from typing import Any

from runtime.provider import generate


class Agent:
    """Identify material risks, uncertainties, assumptions, and missing evidence."""

    name = 'risk_analyst'
    role = 'risk analysis'

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run independently through the generated project's provider client."""
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dictionary")
        missing = [key for key in ['verified_evidence', 'market_analysis'] if key not in inputs]
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")
        prompt = (
            f"You are the {self.role} agent '{self.name}'.\n"
            f"Purpose: Identify material risks, uncertainties, assumptions, and missing evidence.\n"
            f"Requested task inputs: {inputs!r}\n"
            "Return a useful response that satisfies the agent purpose."
        )
        response = generate(prompt)
        if not response.text.strip():
            raise RuntimeError("provider returned an empty response")
        return {"status": "completed", "agent": self.name, "provider": response.provider, "model": response.model, "response": response.text}
