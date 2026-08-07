"""Command-line interface for building AI agents from natural-language goals."""

import argparse
import re
from pathlib import Path

from .agents.factory_agent import FactoryAgent
from .materializer.filesystem import FileSystemMaterializer


def _workspace_name(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return value or "generated-agent"


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Factory")
    parser.add_argument("goal", help="Describe the AI system to build")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Directory where the generated agent project will be written",
    )
    args = parser.parse_args()

    factory = FactoryAgent()
    design = factory.design_and_scaffold(args.goal)

    workspace = Path(args.workspace) if args.workspace else Path("generated") / _workspace_name(design.spec.name)
    written = FileSystemMaterializer().materialize(workspace, design.files)

    print(f"agent: {design.spec.name}")
    print(f"purpose: {design.spec.purpose}")
    print(f"workspace: {workspace.resolve()}")
    print(f"files: {len(written)}")
    for path in written:
        print(f"created: {path.relative_to(workspace.resolve())}")


if __name__ == "__main__":
    main()
