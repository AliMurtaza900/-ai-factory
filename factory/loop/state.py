"""State machine for a bounded agent-build lifecycle."""

from dataclasses import dataclass, field
from enum import Enum


class LoopStage(str, Enum):
    SPECIFY = "specify"
    BUILD = "build"
    EVALUATE = "evaluate"
    IMPROVE = "improve"
    APPROVE = "approve"
    FAILED = "failed"
    COMPLETE = "complete"


@dataclass
class LoopState:
    stage: LoopStage = LoopStage.SPECIFY
    iteration: int = 0
    max_iterations: int = 3
    history: list[str] = field(default_factory=list)

    def transition(self, stage: LoopStage, note: str = "") -> None:
        self.stage = stage
        if note:
            self.history.append(note)

    def can_retry(self) -> bool:
        return self.iteration < self.max_iterations

    def next_iteration(self) -> None:
        self.iteration += 1
        if self.iteration > self.max_iterations:
            raise RuntimeError("Improvement iteration limit exceeded")
