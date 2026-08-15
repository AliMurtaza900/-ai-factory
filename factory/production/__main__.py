"""CLI for the production video pipeline."""

import argparse
import json

from .job import JobStore
from .orchestrator import run_video_factory
from .pipeline import ProductionPipeline
from .video import CommandVideoAdapter


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a resumable AI Factory video job")
    parser.add_argument("goal")
    parser.add_argument("--workspace", default="data/workspaces")
    parser.add_argument("--state-dir", default="data/jobs")
    args = parser.parse_args()
    result = run_video_factory(
        args.goal,
        adapter=CommandVideoAdapter.from_environment(),
        pipeline=ProductionPipeline(
            store=JobStore(args.state_dir),
            workspace_root=args.workspace,
        ),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
