"""Safe behavior-test contract for generated agents.

Behavior tests use an explicitly supplied isolated runner. The Factory never
executes generated code directly on its host.
"""

from dataclasses import dataclass
from typing import Callable

from ..sandbox.runner import ExecutionResult, SandboxRunner
from ..sandbox.policy import SandboxPolicy


@dataclass(frozen=True)
class BehaviorCase:
    name: str
    command: list[str]
    expect_exit_code: int = 0
    required_output: str | None = None


@dataclass(frozen=True)
class BehaviorReport:
    passed: bool
    cases: list[str]
    failures: list[str]


def run_behavior_tests(
    runner: SandboxRunner,
    cases: list[BehaviorCase],
    *,
    policy: SandboxPolicy,
    output_validator: Callable[[BehaviorCase, ExecutionResult], bool] | None = None,
) -> BehaviorReport:
    failures: list[str] = []
    completed: list[str] = []

    for case in cases:
        try:
            result = runner.run(case.command, policy=policy)
        except Exception as exc:
            failures.append(f"{case.name}: runner error: {exc}")
            continue

        completed.append(case.name)
        if result.timed_out:
            failures.append(f"{case.name}: timed out")
            continue
        if result.return_code != case.expect_exit_code:
            failures.append(f"{case.name}: exit code {result.return_code}, expected {case.expect_exit_code}")
            continue
        if case.required_output is not None and case.required_output not in result.stdout:
            failures.append(f"{case.name}: required output was not produced")
            continue
        if output_validator is not None and not output_validator(case, result):
            failures.append(f"{case.name}: output validator rejected result")

    return BehaviorReport(not failures, completed, failures)
