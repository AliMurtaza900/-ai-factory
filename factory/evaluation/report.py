"""Human- and machine-readable evaluation report formatting."""

import json

from .models import EvaluationReport


def report_to_dict(report: EvaluationReport) -> dict:
    return {
        "agent_name": report.agent_name,
        "passed": report.passed,
        "score": report.score,
        "results": [
            {
                "test_name": result.test_name,
                "status": result.status.value,
                "passed": result.passed,
                "message": result.message,
                "actual": result.actual,
                "expected": result.expected,
            }
            for result in report.results
        ],
    }


def report_to_json(report: EvaluationReport) -> str:
    return json.dumps(report_to_dict(report), indent=2, sort_keys=True)
