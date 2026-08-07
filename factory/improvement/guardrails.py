"""Safety limits for iterative agent improvement."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ImprovementLimits:
    max_iterations: int = 3
    max_tasks_per_iteration: int = 10
    require_regression_pass: bool = True

    def validate(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        if self.max_tasks_per_iteration < 1:
            raise ValueError("max_tasks_per_iteration must be at least 1")
