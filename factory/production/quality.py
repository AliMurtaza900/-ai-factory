"""Deterministic quality gates for generated video jobs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def validate_video_result(result: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Validate the adapter contract before a job is marked publishable."""
    if result.get("status") != "completed":
        raise ValueError("video result is not completed")
    video = result.get("video") or result.get("video_path")
    if video:
        path = Path(video)
        if not path.is_absolute():
            path = workspace / path
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"video artifact missing or empty: {path}")
    for key in ("title", "description"):
        if key in result and not str(result[key]).strip():
            raise ValueError(f"video metadata field is empty: {key}")
    return {"status": "approved", "checks": ["adapter-contract", "artifact", "metadata"]}


def validate_upload_result(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") != "completed":
        raise ValueError("upload result is not completed")
    video_id = result.get("video_id") or result.get("youtube_video_id")
    if not video_id:
        raise ValueError("successful upload must return video_id")
    return {"status": "approved", "video_id": str(video_id)}
