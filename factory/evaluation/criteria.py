"""Acceptance-criteria checks for generated agent specifications."""

from typing import Any

from ..specs.agent_spec import AgentSpec
from .models import EvaluationStatus, TestResult


def validate_spec_criteria(spec: AgentSpec) -> list[TestResult]:
    """Turn structural acceptance requirements into initial evaluation results."""
    results: list[TestResult] = []
    checks: list[tuple[str, bool, str]] = [
        (
            "required purpose",
            bool(spec.purpose.strip()),
            "Purpose is defined" if spec.purpose.strip() else "Purpose is missing",
        ),
        (
            "required outputs",
            bool(spec.outputs),
            "At least one output is defined" if spec.outputs else "No outputs defined",
        ),
        (
            "acceptance criteria",
            bool(spec.acceptance_criteria),
            "Acceptance criteria are defined"
            if spec.acceptance_criteria
            else "No acceptance criteria defined",
        ),
    ]
    for name, passed, message in checks:
        results.append(
            TestResult(
                test_name=name,
                status=EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED,
                passed=passed,
                message=message,
            )
        )
    return results
