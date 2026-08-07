from factory.evaluation.models import EvaluationReport, EvaluationStatus, TestResult
from factory.improvement.engine import ImprovementEngine


def test_failed_evaluation_creates_actionable_plan() -> None:
    report = EvaluationReport(
        agent_name="demo-agent",
        results=[
            TestResult(
                test_name="basic",
                status=EvaluationStatus.FAILED,
                passed=False,
                message="Output mismatch",
                actual={"answer": "wrong"},
                expected={"answer": "right"},
            )
        ],
    )
    cycle = ImprovementEngine().analyze(report)
    assert cycle.plan.actionable
    assert cycle.plan.tasks[0].priority.value == "high"
