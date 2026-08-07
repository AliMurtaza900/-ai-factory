import unittest

from factory.evaluation.models import EvaluationReport, EvaluationStatus, TestResult
from factory.improvement.engine import ImprovementEngine


class ImprovementLoopTest(unittest.TestCase):
    def test_failed_evaluation_creates_actionable_plan(self) -> None:
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
        self.assertTrue(cycle.plan.actionable)
        self.assertEqual(cycle.plan.tasks[0].priority.value, "high")


if __name__ == "__main__":
    unittest.main()
