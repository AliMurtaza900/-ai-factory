"""Team specification and deterministic orchestration for generated agents."""

from dataclasses import dataclass, field
from typing import Any

from ..specs.agent_spec import AgentSpec


@dataclass(frozen=True)
class TeamMember:
    name: str
    role: str
    purpose: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    def to_agent_spec(self) -> AgentSpec:
        return AgentSpec(
            name=self.name,
            purpose=self.purpose,
            role=self.role,
            inputs=list(self.inputs),
            outputs=list(self.outputs),
            acceptance_criteria=[f"Produces the required {output}" for output in self.outputs] or ["Completes its assigned role"],
        )


@dataclass
class AgentTeam:
    goal: str
    members: list[TeamMember] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.goal.strip():
            errors.append("team goal is required")
        if not self.members:
            errors.append("at least one team member is required")
        names = [member.name.strip().lower() for member in self.members]
        if len(names) != len(set(names)):
            errors.append("team member names must be unique")
        produced: set[str] = set()
        for index, member in enumerate(self.members, start=1):
            label = member.name or "<unnamed>"
            if not member.name.strip(): errors.append("team member name is required")
            if not member.role.strip(): errors.append(f"role is required for {label}")
            if not member.purpose.strip(): errors.append(f"purpose is required for {label}")
            if not member.outputs: errors.append(f"at least one output is required for {label}")
            missing = [item for item in member.inputs if item not in produced]
            if index > 1 and missing:
                errors.append(f"{label}: missing upstream inputs: {', '.join(missing)}")
            produced.update(member.outputs)
        return errors

    def agent_specs(self) -> list[AgentSpec]:
        return [member.to_agent_spec() for member in self.members]

    def plan(self) -> list[dict[str, Any]]:
        steps = []
        produced: set[str] = set()
        for index, member in enumerate(self.members, start=1):
            missing = [item for item in member.inputs if item not in produced]
            steps.append({"order": index, "agent": member.name, "role": member.role, "inputs": list(member.inputs), "outputs": list(member.outputs), "missing_inputs": missing})
            produced.update(member.outputs)
        return steps
