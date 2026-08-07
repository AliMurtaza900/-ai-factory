"""Small CLI for starting a Factory job."""

import argparse
import json

from .agents.factory_agent import FactoryAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Factory")
    parser.add_argument("goal", help="Natural-language goal for the agent to build")
    args = parser.parse_args()
    result = FactoryAgent().design_and_scaffold(args.goal)
    print(json.dumps({
        "agent": result.spec.to_dict(),
        "generated_files": [file.path for file in result.files],
    }, indent=2))


if __name__ == "__main__":
    main()
