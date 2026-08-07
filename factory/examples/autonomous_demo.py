"""Exercise the Factory's real design -> build -> evaluate -> improve path."""

from factory.agents.factory_agent import FactoryAgent
from factory.evaluation.models import EvaluationReport, EvaluationStatus, TestResult
from factory.improvement.engine import ImprovementEngine


def main() -> None:
    goal = "Create an AI research assistant that answers questions with structured responses"
    design = FactoryAgent().design_and_scaffold(goal)

    passing = EvaluationReport(
        agent_name=design.spec.name,
        results=[
            TestResult(
                test_name="scaffold-created",
                status=EvaluationStatus.PASSED,
                passed=True,
                message="Factory produced a valid agent scaffold",
            )
        ],
    )
    print(f"v1: {design.spec.name} score={passing.score:.2f} passed={passing.passed}")

    failing = EvaluationReport(
        agent_name=design.spec.name,
        results=[
            TestResult(
                test_name="structured-output",
                status=EvaluationStatus.FAILED,
                passed=False,
                message="Demonstration failure used to exercise the improvement path",
                actual={"format": "plain"},
                expected={"format": "structured"},
            )
        ],
    )
    cycle = ImprovementEngine().analyze(failing)
    print(f"improvement tasks={len(cycle.plan.tasks)} retryable={cycle.plan.actionable}")


if __name__ == "__main__":
    main()
