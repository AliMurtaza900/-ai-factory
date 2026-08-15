"""High-level autonomous video production orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .pipeline import ProductionPipeline, Stage
from .quality import validate_upload_result, validate_video_result
from .video import VideoAdapter


def run_video_factory(
    goal: str,
    *,
    adapter: VideoAdapter,
    pipeline: ProductionPipeline | None = None,
    workspace_root: str | Path = "data/workspaces",
) -> dict[str, Any]:
    """Run an existing generator/uploader as a resumable Factory job.

    The adapter is intentionally the boundary: the Factory owns scheduling,
    persistence, retries and quality gates while the user's existing media
    stack owns rendering, credentials and YouTube-specific implementation.
    """
    pipeline = pipeline or ProductionPipeline(workspace_root=workspace_root)

    def produce(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        return adapter.run(goal, workspace)

    def video_qc(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        return validate_video_result(context["produce_video"], workspace)

    def upload_qc(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        result = context["produce_video"]
        if not (result.get("video_id") or result.get("youtube_video_id")):
            raise RuntimeError("adapter must upload the video and return video_id")
        return validate_upload_result(result)

    job = pipeline.run(
        goal,
        [
            Stage("produce_video", produce, retries=2),
            Stage("video_qc", video_qc, retries=1),
            Stage("upload_qc", upload_qc, retries=1),
        ],
    )
    return {
        "status": job.status,
        "job_id": job.job_id,
        "goal": job.goal,
        "stages": {name: state.output for name, state in job.stages.items()},
    }
