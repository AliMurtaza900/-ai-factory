"""Single-command end-to-end Factory workflow."""

from dataclasses import dataclass
from pathlib import Path
import json

from .autonomous import AutonomousFactory
from .learning.pattern_store import PatternStore, SuccessfulPattern


@dataclass(frozen=True)
class ProductionResult:
    goal: str
    passed: bool
    attempts: int
    output_dir: Path
    reused_patterns: int


def run_factory(goal: str, *, output_root: str | Path = "generated", max_attempts: int = 2) -> ProductionResult:
    if not goal or not goal.strip():
        raise ValueError("A non-empty goal is required")

    store = PatternStore()
    reused = len(store.relevant(goal.strip()))
    result = AutonomousFactory().run(goal.strip(), max_attempts=max_attempts)

    safe_name = result.design.spec.name.strip() or "generated-agent"
    output_dir = Path(output_root) / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)
    for generated in result.design.files:
        path = output_dir / generated.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(generated.content, encoding="utf-8")

    (output_dir / "SPEC.json").write_text(
        json.dumps(result.design.spec.to_dict(), indent=2), encoding="utf-8"
    )

    if result.passed:
        store.record(SuccessfulPattern(
            goal=goal.strip(),
            agent_name=result.design.spec.name,
            capabilities=result.design.spec.capabilities,
            acceptance_criteria=result.design.spec.acceptance_criteria,
        ))

    return ProductionResult(goal.strip(), result.passed, result.attempts, output_dir, reused)
