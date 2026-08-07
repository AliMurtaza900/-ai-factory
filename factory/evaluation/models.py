"""Models for deterministic agent evaluation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvaluationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class TestCase:
    name: str
    inputs: dict[str, Any]
    expected: dict[str, Any] | None = None
    description: str = ""


@dataclass
class TestResult:
    test_name: str
    status: EvaluationStatus
    passed: bool
    message: str = ""
    actual: dict[str, Any] | None = None
    expected: dict[str, Any] | None = None


@dataclass
class EvaluationReport:
    agent_name: str
    results: list[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(result.passed for result in self.results)

    @property
    def score(self) -> float:
        if not self.results:
            return 0.0
        return sum(result.passed for result in self.results) / len(self.results)
