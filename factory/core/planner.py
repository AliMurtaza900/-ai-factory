"""Baseline planner used before an LLM-backed planner is connected."""

from .models import FactoryJob, PlanStep


def baseline_plan(job: FactoryJob) -> list[PlanStep]:
    """Return a safe, provider-independent plan for a new AI system."""
    return [
        PlanStep(
            name="specify",
            description=f"Turn the goal into a precise system specification: {job.goal}",
            order=1,
            agent_role="architect",
            outputs=["specification"],
        ),
        PlanStep(
            name="build",
            description="Generate the initial implementation from the specification.",
            order=2,
            agent_role="builder",
            inputs=["specification"],
            outputs=["implementation"],
        ),
        PlanStep(
            name="test",
            description="Run automated validation and record failures.",
            order=3,
            agent_role="tester",
            inputs=["implementation"],
            outputs=["test_report"],
        ),
        PlanStep(
            name="improve",
            description="Use test results to propose and apply targeted improvements.",
            order=4,
            agent_role="improver",
            inputs=["implementation", "test_report"],
            outputs=["revised_implementation"],
        ),
    ]
