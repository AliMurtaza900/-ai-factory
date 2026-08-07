"""Small persistent store for successful, reusable Factory patterns."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class SuccessfulPattern:
    goal: str
    agent_name: str
    capabilities: list[str]
    acceptance_criteria: list[str]


class PatternStore:
    def __init__(self, path: str | Path = ".factory/patterns.json") -> None:
        self.path = Path(path)

    def load(self) -> list[SuccessfulPattern]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [SuccessfulPattern(**item) for item in raw]
        except (OSError, ValueError, TypeError):
            return []

    def record(self, pattern: SuccessfulPattern) -> None:
        patterns = self.load()
        key = (pattern.goal.strip().lower(), pattern.agent_name)
        patterns = [p for p in patterns if (p.goal.strip().lower(), p.agent_name) != key]
        patterns.append(pattern)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([asdict(p) for p in patterns[-50:]], indent=2), encoding="utf-8")

    def relevant(self, goal: str, limit: int = 3) -> list[SuccessfulPattern]:
        terms = set(goal.lower().split())
        scored = []
        for pattern in self.load():
            score = len(terms & set(pattern.goal.lower().split()))
            if score:
                scored.append((score, pattern))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [pattern for _, pattern in scored[:limit]]
