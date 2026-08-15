"""Durable autonomous production queue built on the resumable pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import threading
from typing import Any

from .job import JobStore
from .orchestrator import ProductionOrchestrator


@dataclass
class QueueItem:
    goal: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "queued"
    job_id: str | None = None


class ProductionQueue:
    """File-backed FIFO queue that survives process restarts."""

    def __init__(self, path: str | Path = "data/production_queue.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _load(self) -> list[QueueItem]:
        if not self.path.exists():
            return []
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        return [QueueItem(**item) for item in raw]

    def _save(self, items: list[QueueItem]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps([item.__dict__ for item in items], indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def enqueue(self, goal: str, metadata: dict[str, Any] | None = None) -> QueueItem:
        if not goal.strip():
            raise ValueError("goal must be non-empty")
        with self._lock:
            item = QueueItem(goal=goal.strip(), metadata=metadata or {})
            items = self._load()
            items.append(item)
            self._save(items)
            return item

    def pending(self) -> list[QueueItem]:
        with self._lock:
            return [x for x in self._load() if x.status == "queued"]

    def run_next(self, orchestrator: ProductionOrchestrator) -> QueueItem | None:
        with self._lock:
            items = self._load()
            index = next((i for i, x in enumerate(items) if x.status == "queued"), None)
            if index is None:
                return None
            item = items[index]
            item.status = "running"
            self._save(items)
        try:
            job = orchestrator.run(item.goal, metadata=item.metadata)
            item.job_id = job.job_id
            item.status = "completed"
        except Exception:
            item.status = "failed"
            raise
        finally:
            with self._lock:
                items = self._load()
                for current in items:
                    if current.goal == item.goal and current.status == "running":
                        current.status = item.status
                        current.job_id = item.job_id
                        break
                self._save(items)
        return item
