"""Registry records for generated agents and their versions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentVersion:
    version: int
    spec: dict
    files: list[str] = field(default_factory=list)
    score: float | None = None
    approved: bool = False
    created_at: str = field(default_factory=utc_now)
    notes: list[str] = field(default_factory=list)


@dataclass
class AgentRecord:
    agent_id: str
    name: str
    versions: list[AgentVersion] = field(default_factory=list)

    @property
    def latest(self) -> AgentVersion | None:
        return self.versions[-1] if self.versions else None
