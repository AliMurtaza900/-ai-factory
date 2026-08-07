"""Demonstrate bounded evaluate -> improve -> re-evaluate behavior."""

from factory.builder.project import AgentProjectBuilder, GeneratedFile
from factory.evaluation.factory_evaluator import FactoryEvaluator
from factory.improvement.applier import ImprovementApplier
from factory.specs.agent_spec import AgentSpec


def main() -> None:
    spec = AgentSpec(
        name="self-improving-agent",
        purpose="Demonstrate bounded self-improvement",
        role="test agent",
        inputs=["user_request"],
        outputs=["agent_response"],
        acceptance_criteria=["Generated runtime has the required contract"],
    )
    files = AgentProjectBuilder().build(spec)

    # Deliberately introduce one safe, local defect for the demo.
    broken = [
        GeneratedFile(f.path, f.content.replace("def run", "def broken_run", 1) if f.path.endswith("/agent.py") else f.content)
        for f in files
    ]

    def repair(current: list[GeneratedFile], _proposals: list[str]) -> list[GeneratedFile]:
        return [
            GeneratedFile(f.path, f.content.replace("def broken_run", "def run", 1) if f.path.endswith("/agent.py") else f.content)
            for f in current
        ]

    result = ImprovementApplier(FactoryEvaluator(), max_iterations=2).improve(spec, broken, repair)
    print(f"before: passed={FactoryEvaluator().evaluate(spec, broken).passed}")
    print(f"after: passed={result.report.passed} iterations={result.iterations} changed={result.changed}")


if __name__ == "__main__":
    main()
