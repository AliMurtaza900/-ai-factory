"""High-level Factory Agent facade."""

from dataclasses import dataclass

from ..builder.project import GeneratedFile
from ..specs.agent_spec import AgentSpec
from .architect import ArchitectAgent
from .builder_agent import BuilderAgent


@dataclass
class FactoryDesign:
    spec: AgentSpec
    files: list[GeneratedFile]


class FactoryAgent:
    """Turn a natural-language goal into an approved build candidate."""

    def __init__(self) -> None:
        self.architect = ArchitectAgent()
        self.builder = BuilderAgent()

    def design_and_scaffold(self, goal: str) -> FactoryDesign:
        spec = self.architect.design(goal)
        errors = spec.validate()
        if errors:
            raise ValueError("Architect produced invalid spec: " + "; ".join(errors))
        files = self.builder.build(spec)
        return FactoryDesign(spec=spec, files=files)
