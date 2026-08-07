"""Deterministic evaluation of generated Factory projects."""

import ast
import json

from .models import EvaluationReport, EvaluationStatus, TestResult
from ..builder.project import GeneratedFile
from ..specs.agent_spec import AgentSpec


class FactoryEvaluator:
    """Evaluate generated artifacts without requiring an external AI provider."""

    def evaluate(self, spec: AgentSpec, files: list[GeneratedFile]) -> EvaluationReport:
        results: list[TestResult] = []
        by_path = {file.path: file.content for file in files}

        results.append(self._required_files(by_path))
        results.append(self._python_syntax(by_path))
        results.append(self._spec_matches(spec, by_path))
        results.append(self._runtime_contract(by_path))
        return EvaluationReport(agent_name=spec.name, results=results)

    @staticmethod
    def _required_files(files: dict[str, str]) -> TestResult:
        required = {"__init__.py", "agent.py", "SPEC.json", "README.md"}
        found = {path.rsplit("/", 1)[-1] for path in files}
        missing = sorted(required - found)
        return TestResult(
            test_name="required-artifacts",
            status=EvaluationStatus.PAUSED if False else (EvaluationStatus.FAILED if missing else EvaluationStatus.PASSED),
            passed=not missing,
            message="missing files: " + ", ".join(missing) if missing else "all required artifacts present",
        )

    @staticmethod
    def _python_syntax(files: dict[str, str]) -> TestResult:
        errors = []
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    ast.parse(content, filename=path)
                except SyntaxError as exc:
                    errors.append(f"{path}: {exc}")
        return TestResult(
            test_name="python-syntax",
            status=EvaluationStatus.FAILED if errors else EvaluationStatus.PASSED,
            passed=not errors,
            message="; ".join(errors) if errors else "generated Python parses successfully",
        )

    @staticmethod
    def _spec_matches(spec: AgentSpec, files: dict[str, str]) -> TestResult:
        matches = [path for path in files if path.endswith("/SPEC.json")]
        if not matches:
            return TestResult("spec-consistency", EvaluationStatus.FAILED, False, "SPEC.json missing")
        try:
            generated = json.loads(files[matches[0]])
            expected = spec.to_dict()
            passed = all(generated.get(key) == value for key, value in expected.items())
            message = "generated spec matches the approved AgentSpec" if passed else "generated SPEC.json differs from approved AgentSpec"
        except Exception as exc:
            passed = False
            message = f"invalid SPEC.json: {exc}"
        return TestResult("spec-consistency", EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED, passed, message)

    @staticmethod
    def _runtime_contract(files: dict[str, str]) -> TestResult:
        agents = [content for path, content in files.items() if path.endswith("/agent.py")]
        if not agents:
            return TestResult("runtime-contract", EvaluationStatus.FAILED, False, "agent.py missing")
        content = agents[0]
        required = ["class Agent", "def run", "configured_provider", "return {"]
        missing = [item for item in required if item not in content]
        return TestResult(
            "runtime-contract",
            EvaluationStatus.PASSED if not missing else EvaluationStatus.FAILED,
            not missing,
            "runtime contract present" if not missing else "missing runtime elements: " + ", ".join(missing),
        )
