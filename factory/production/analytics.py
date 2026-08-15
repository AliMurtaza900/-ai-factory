"""Local feedback store for post-publication optimization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VideoMetric:
    video_id: str
    views: int = 0
    ctr: float | None = None
    retention: float | None = None
    likes: int = 0
    comments: int = 0
    revenue: float | None = None


class FeedbackStore:
    def __init__(self, path: str | Path = "data/video_metrics.json") -> None:
        self.path = Path(path)

    def record(self, metric: VideoMetric) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = self.all()
        records.append(metric)
        self.path.write_text(json.dumps([asdict(x) for x in records], indent=2) + "\n", encoding="utf-8")

    def all(self) -> list[VideoMetric]:
        if not self.path.exists():
            return []
        return [VideoMetric(**item) for item in json.loads(self.path.read_text(encoding="utf-8"))]

    def summarize(self) -> dict[str, Any]:
        records = self.all()
        if not records:
            return {"videos": 0, "views": 0}
        ctrs = [x.ctr for x in records if x.ctr is not None]
        ret = [x.retention for x in records if x.retention is not None]
        return {
            "videos": len(records),
            "views": sum(x.views for x in records),
            "average_ctr": sum(ctrs) / len(ctrs) if ctrs else None,
            "average_retention": sum(ret) / len(ret) if ret else None,
            "likes": sum(x.likes for x in records),
            "comments": sum(x.comments for x in records),
        }

    def rank(self) -> list[VideoMetric]:
        """Rank outcomes without pretending correlation is causation."""
        return sorted(self.all(), key=lambda x: (x.views, x.retention or 0.0, x.ctr or 0.0), reverse=True)
