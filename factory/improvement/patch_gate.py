"""Safely gate model-proposed changes behind validation.

This first implementation is intentionally conservative: model output is treated as
proposal text, never executable code. A proposal is accepted only when an external
validator reports success.
"""

from dataclasses import dataclass
from typing import Callable, Sequence


@dataclass(frozen=True)
class PatchDecision:
    accepted: bool
    proposals: list[str]
    reason: str


class PatchGate:
    """Bounded proposal gate; never executes model output directly."""

    def __init__(self, validator: Callable[[], bool], max_proposals: int = 10) -> None:
        self.validator = validator
        self.max_proposals = max_proposals

    def evaluate(self, proposals: Sequence[str]) -> PatchDecision:
        bounded = [p.strip() for p in proposals if p and p.strip()][: self.max_proposals]
        if not bounded:
            return PatchDecision(False, [], "No actionable proposals")
        if self.validator():
            return PatchDecision(True, bounded, "Validation passed")
        return PatchDecision(False, bounded, "Validation failed; proposal rejected")
