"""Command-line interface for the end-to-end AI Factory workflow."""

import argparse

from .run import run_factory


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Factory")
    parser.add_argument("goal", help="Describe the AI system to build")
    parser.add_argument("--workspace", default="generated", help="Root directory for generated agents")
    parser.add_argument("--max-attempts", type=int, default=2, help="Maximum bounded Factory attempts")
    args = parser.parse_args()

    result = run_factory(args.goal, output_root=args.workspace, max_attempts=args.max_attempts)
    print(f"agent: {result.goal}")
    print(f"passed: {result.passed}")
    print(f"attempts: {result.attempts}")
    print(f"reused_patterns: {result.reused_patterns}")
    print(f"output: {result.output_dir.resolve()}")

    if not result.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
