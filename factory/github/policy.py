"""Guardrails for factory-driven GitHub changes."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubAutomationPolicy:
    """Conservative defaults for autonomous repository operations."""

    allowed_branches: tuple[str, ...] = ("factory/",)
    require_pull_request: bool = True
    allow_force_push: bool = False
    allow_delete: bool = False

    def validate_branch(self, branch: str) -> None:
        if not any(branch.startswith(prefix) for prefix in self.allowed_branches):
            raise ValueError(f"Branch is outside factory policy: {branch}")
