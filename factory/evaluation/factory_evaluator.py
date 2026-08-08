"""Deterministic evaluation of generated Factory projects."""

import ast
import json

from .models import EvaluationReport, EvaluationStatus, TestResult
from ..builder.project import GeneratedFile
from ..specs.agent_spec import AgentSpec


class FactoryEvaluator:
    """Evaluate generated artifacts without requiring an external AI provider."""

    def evaluate(self, spec: AgentSpec, files: list[GeneratedFile]) -> EvaluationReport:
        by_path = {file.path: file.content for file in files}
        results = [self._required_files(by_path), self._python_syntax(by_path), self._spec_matches(spec, by_path), self._runtime_contract(by_path)]
        return EvaluationReport(agent_name=spec.name, results=results)

    @staticmethod
    def _required_files(files: dict[str, str]) -> TestResult:
        required = {"__init__.py", "agent.py", "SPEC.json", "README.md"}
        agent_paths = [path for path in files if path.startswith("agents/")]
        found = {path.rsplit("/", 1)[-1] for path in agent_paths}
        missing = sorted(required - found)
        return TestResult("required-artifacts", EvaluationStatus.FAILED if missing else EvaluationStatus.PASSED, not missing, "missing files: " + ", ".join(missing) if missing else "all required artifacts present")

    @staticmethod
    def _python_syntax(files: dict[str, str]) -> TestResult:
        errors = []
        for path, content in files.items():
            if path.endswith(".py"):
                try:
                    ast.parse(content, filename=path)
                except SyntaxError as exc:
                    errors.append(f"{path}: {exc}")
        return TestResult("python-syntax", EvaluationStatus.FAILED if errors else EvaluationStatus.PASSED, not errors, "; ".join(errors) if errors else "generated Python parses successfully")

    @staticmethod
    def _spec_matches(spec: AgentSpec, files: dict[str, str]) -> TestResult:
        matches = [path for path in files if path.startswith("agents/") and path.endswith("/SPEC.json")]
        if not matches:
            return TestResult("spec-consistency", EvaluationStatus.FAILED, False, "SPEC.json missing")
        try:
            generated = json.loads(files[matches[0]])
            expected = spec.to_dict()
            mismatches = [key for key, value in expected.items() if generated.get(key) != value]
            passed = not mismatches
            message = "generated spec matches the approved AgentSpec" if passed else "mismatched fields: " + ", ".join(mismatches)
        except Exception as exc:
            passed = False
            message = f"invalid SPEC.json: {exc}"
        return TestResult("spec-consistency", EvaluationStatus.PASSED if passed else EvaluationStatus.FAILED, passed, message)

    @staticmethod
    def _runtime_contract(files: dict[str, str]) -> TestResult:
        agent_paths = [path for path in files if path.startswith("agents/") and path.endswith("/agent.py")]
        if not agent_paths:
            return TestResult("runtime-contract", EvaluationStatus.FAILED, False, "agent.py missing")
        if "runtime/provider.py" not in files:
            return TestResult("runtime-contract", EvaluationStatus.FAILED, False, "runtime/provider.py missing")
        failures = []
        for path in agent_paths:
            content = files[path]
            if "configured_provider" in content or "from factory.providers.factory" in content or "import factory" in content:
                failures.append(f"{path}: imports Factory runtime")
            if "from runtime.provider import generate" not in content:
                failures.append(f"{path}: missing standalone provider import")
            if "class Agent" not in content or "def run" not in content:
                failures.append(f"{path}: missing Agent/run contract")
        if failures:
            return TestResult("runtime-contract", EvaluationStatus.FAILED, False, "; ".join(failures))
        return TestResult("runtime-contract", EvaluationStatus.PASSED, True, "all generated agents use bundled standalone runtime")
