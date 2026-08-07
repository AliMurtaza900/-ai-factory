"""Builder role wrapping the deterministic project builder."""

from ..builder.project import AgentProjectBuilder, GeneratedFile
from ..specs.agent_spec import AgentSpec


class BuilderAgent:
    role = "builder"

    def __init__(self, builder: AgentProjectBuilder | None = None) -> None:
        self.builder = builder or AgentProjectBuilder()

    def build(self, spec: AgentSpec) -> list[GeneratedFile]:
        return self.builder.build(spec)
