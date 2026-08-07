"""Command-line entry point for the first AI Factory milestone."""

import argparse
import uuid

from .core.models import FactoryJob
from .core.orchestrator import FactoryOrchestrator
from .core.planner import baseline_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Factory")
    parser.add_argument("goal", help="Describe the AI system to build")
    args = parser.parse_args()

    job = FactoryJob(goal=args.goal, job_id=str(uuid.uuid4()))
    result = FactoryOrchestrator(baseline_plan).run(job)

    print(f"job_id: {result.job_id}")
    print(f"status: {result.status.value}")
    for step in result.metadata.get("plan", []):
        print(f"{step['order']}. {step['name']} [{step['agent_role']}] - {step['description']}")


if __name__ == "__main__":
    main()
