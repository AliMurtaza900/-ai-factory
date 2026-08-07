"""Represent proposed GitHub changes before they are published."""

from dataclasses import dataclass, field

from ..builder.project import GeneratedFile
from .policy import GitHubAutomationPolicy


@dataclass
class GitHubChangeSet:
    branch: str
    title: str
    files: list[GeneratedFile] = field(default_factory=list)

    def validate(self, policy: GitHubAutomationPolicy) -> None:
        policy.validate_branch(self.branch)
        if not self.title.strip():
            raise ValueError("Change-set title is required")
        if not self.files:
            raise ValueError("Change-set must contain at least one file")
