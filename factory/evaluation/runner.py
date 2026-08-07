"""Controlled in-process evaluation runner.

This runner only executes an explicitly supplied callable. It does not execute
arbitrary source code from generated files. A future sandbox adapter can expose
isolated execution with resource and network limits.
"""

from collections.abc import Callable, Iterable
from typing import Any

from .models import EvaluationReport, EvaluationStatus, TestCase, TestResult


AgentCallable = Callable[[dict[str, Any]], dict[str, Any]]


class EvaluationRunner:
    """Run explicit test cases against an agent callable."""

    def run(
        self,
        agent_name: str,
        agent: AgentCallable,
        cases: Iterable[TestCase],
    ) -> EvaluationReport:
        report = EvaluationReport(agent_name=agent_name)
        for case in cases:
            try:
                actual = agent(case.inputs)
                passed = self._matches(case.expected, actual)
                report.results.append(
                    TestResult(
                        test_name=case.name,
                        status=EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED,
                        passed=passed,
                        message="Output matched expectation" if passed else "Output mismatch",
                        actual=actual,
                        expected=case.expected,
                    )
                )
            except Exception as exc:
                report.results.append(
                    TestResult(
                        test_name=case.name,
                        status=EvaluationStatus.FAILED,
                        passed=False,
                        message=f"Agent raised {type(exc).__name__}: {exc}",
                        expected=case.expected,
                    )
                )
        return report

    @staticmethod
    def _matches(expected: dict[str, Any] | None, actual: dict[str, Any]) -> bool:
        if expected is None:
            return True
        return all(actual.get(key) == value for key, value in expected.items())
