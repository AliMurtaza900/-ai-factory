"""Durable, restart-safe job state for production workflows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StageState:
    name: str
    status: str = "pending"
    attempts: int = 0
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    output: dict[str, Any] = field(default_factory=dict)


@dataclass
class JobState:
    job_id: str
    goal: str
    status: str = "pending"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    stages: dict[str, StageState] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = _now()

    def stage(self, name: str) -> StageState:
        return self.stages.setdefault(name, StageState(name=name))


class JobStore:
    """Atomic JSON persistence; no external database is required."""

    def __init__(self, root: str | Path = "data/jobs") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, job_id: str) -> Path:
        safe = "".join(c for c in job_id if c.isalnum() or c in "-_")
        if not safe:
            raise ValueError("invalid job id")
        return self.root / f"{safe}.json"

    def save(self, job: JobState) -> None:
        job.touch()
        target = self.path(job.job_id)
        payload = json.dumps(asdict(job), indent=2, sort_keys=True) + "\n"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=target.parent, delete=False) as tmp:
            tmp.write(payload)
            temp = Path(tmp.name)
        temp.replace(target)

    def load(self, job_id: str) -> JobState:
        raw = json.loads(self.path(job_id).read_text(encoding="utf-8"))
        stages = {name: StageState(**value) for name, value in raw.pop("stages", {}).items()}
        return JobState(stages=stages, **raw)
