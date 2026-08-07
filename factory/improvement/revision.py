"""Turn improvement proposals into reviewable file revisions."""

from dataclasses import dataclass

from .models import ImprovementPlan


@dataclass(frozen=True)
class RevisionProposal:
    summary: str
    tasks: tuple[str, ...]
    requires_approval: bool = True


class RevisionPlanner:
    """Create explicit revision proposals without mutating generated projects."""

    def propose(self, plan: ImprovementPlan) -> RevisionProposal:
        tasks = tuple(
            f"{task.title}: {'; '.join(task.proposed_changes)}"
            for task in plan.tasks
        )
        return RevisionProposal(
            summary=f"Improve {plan.agent_name} from score {plan.source_score:.2f}",
            tasks=tasks,
        )
