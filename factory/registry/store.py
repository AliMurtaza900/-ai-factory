"""Small JSON-backed registry suitable for local or CI execution."""

import json
from pathlib import Path

from .models import AgentRecord, AgentVersion


class RegistryStore:
    """Persist agent records without requiring an external database."""

    def __init__(self, path: str | Path = "data/agents.json") -> None:
        self.path = Path(path)

    def _load(self) -> dict[str, AgentRecord]:
        if not self.path.exists():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return {
            key: AgentRecord(
                agent_id=value["agent_id"],
                name=value["name"],
                versions=[AgentVersion(**version) for version in value.get("versions", [])],
            )
            for key, value in raw.items()
        }

    def _save(self, records: dict[str, AgentRecord]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            key: {
                "agent_id": record.agent_id,
                "name": record.name,
                "versions": [version.__dict__ for version in record.versions],
            }
            for key, record in records.items()
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def register_version(
        self,
        agent_id: str,
        name: str,
        spec: dict,
        files: list[str],
        score: float | None = None,
        approved: bool = False,
        notes: list[str] | None = None,
    ) -> AgentVersion:
        records = self._load()
        record = records.setdefault(agent_id, AgentRecord(agent_id=agent_id, name=name))
        version = AgentVersion(
            version=len(record.versions) + 1,
            spec=spec,
            files=files,
            score=score,
            approved=approved,
            notes=notes or [],
        )
        record.versions.append(version)
        self._save(records)
        return version

    def get(self, agent_id: str) -> AgentRecord | None:
        return self._load().get(agent_id)
