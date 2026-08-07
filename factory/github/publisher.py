"""Pure publishing plan for the GitHub automation connector."""

from dataclasses import dataclass

from .changes import GitHubChangeSet
from .policy import GitHubAutomationPolicy


@dataclass(frozen=True)
class PublishPlan:
    branch: str
    title: str
    commit_message: str
    draft_pr: bool


class GitHubPublisher:
    """Prepare a safe publish plan; the connector performs the actual API writes."""

    def __init__(self, policy: GitHubAutomationPolicy | None = None) -> None:
        self.policy = policy or GitHubAutomationPolicy()

    def prepare(self, changes: GitHubChangeSet) -> PublishPlan:
        changes.validate(self.policy)
        return PublishPlan(
            branch=changes.branch,
            title=changes.title,
            commit_message=f"factory: {changes.title}",
            draft_pr=self.policy.require_pull_request,
        )
