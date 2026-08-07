"""Normalize GitHub Actions results into Factory evaluation feedback."""

from dataclasses import dataclass

from ..evaluation.models import EvaluationStatus, EvaluationReport, TestResult


@dataclass(frozen=True)
class CIResult:
    run_id: int
    status: str
    conclusion: str | None

    @property
    def passed(self) -> bool:
        return self.conclusion == "success"


def ci_result_to_report(agent_name: str, result: CIResult) -> EvaluationReport:
    passed = result.passed
    conclusion = result.conclusion or result.status
    return EvaluationReport(
        agent_name=agent_name,
        results=[
            TestResult(
                test_name=f"github-actions:{result.run_id}",
                status=EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED,
                passed=passed,
                message=f"GitHub Actions conclusion: {conclusion}",
            )
        ],
    )
