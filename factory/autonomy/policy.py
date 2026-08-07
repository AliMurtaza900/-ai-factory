"""Safety policy for autonomous revision cycles."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AutonomyPolicy:
    max_revisions: int = 3
    require_ci_pass: bool = True
    require_pr_review: bool = True
    allow_direct_main_writes: bool = False

    def validate(self) -> None:
        if self.max_revisions < 1:
            raise ValueError("max_revisions must be at least 1")
        if self.allow_direct_main_writes:
            raise ValueError("Direct main writes are disabled by default")
