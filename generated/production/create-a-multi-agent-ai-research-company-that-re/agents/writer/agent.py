"""Generated runtime for writer."""

from typing import Any

from runtime.provider import generate


class Agent:
    """Produce a clear executive report from the team's evidence and analysis."""

    name = 'writer'
    role = 'executive writer'

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run independently through the generated project's provider client."""
        missing = [key for key in ['verified_evidence', 'market_analysis', 'risk_assessment'] if key not in inputs]
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")
        prompt = (
            f"You are the {self.role} agent '{self.name}'.\n"
            f"Purpose: Produce a clear executive report from the team's evidence and analysis.\n"
            f"Requested task inputs: {inputs!r}\n"
            "Return a useful response that satisfies the agent purpose."
        )
        response = generate(prompt)
        return {"status": "completed", "agent": self.name, "provider": response.provider, "model": response.model, "response": response.text}
