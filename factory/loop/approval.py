"""Approval policy for moving generated agents beyond evaluation."""

from dataclasses import dataclass

from ..evaluation.models import EvaluationReport


@dataclass(frozen=True)
class ApprovalPolicy:
    require_all_tests_pass: bool = True
    minimum_score: float = 1.0

    def approve(self, report: EvaluationReport) -> bool:
        if self.require_all_tests_pass and not report.passed:
            return False
        return report.score >= self.minimum_score
