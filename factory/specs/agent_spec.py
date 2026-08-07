"""Portable specification for an AI agent produced by the factory."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AgentSpec:
    """The contract the builder must satisfy when creating an agent."""

    name: str
    purpose: str
    role: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    model_provider: str | None = None
    model: str | None = None
    acceptance_criteria: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """Return specification errors instead of raising on user input."""
        errors: list[str] = []
        if not self.name.strip():
            errors.append("name is required")
        if not self.purpose.strip():
            errors.append("purpose is required")
        if not self.role.strip():
            errors.append("role is required")
        if not self.outputs:
            errors.append("at least one output is required")
        if not self.acceptance_criteria:
            errors.append("at least one acceptance criterion is required")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
