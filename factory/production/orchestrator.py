"""High-level autonomous cinematic animated-film orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .cinematic import CinematicPlanner, FilmPlan, validate_cinematic_result
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
    """Turn a simple story idea into a resumable cinematic short-film job.

    The Factory now owns story planning, character/world continuity, complete
    storyboard creation, shot-level QC and targeted regeneration. The adapter
    remains the rendering boundary so the actual animation backend can be
    swapped without changing orchestration or persistence.
    """
    pipeline = pipeline or ProductionPipeline(workspace_root=workspace_root)
    planner = CinematicPlanner()

    def develop_film(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        plan = planner.plan(goal)
        plan_path = plan.write(workspace / "film_plan.json")
        return {
            "title": plan.title,
            "logline": plan.logline,
            "plan_path": str(plan_path),
            "scenes": len({shot.scene_id for shot in plan.shots}),
            "shots": len(plan.shots),
            "characters": [character.id for character in plan.characters],
        }

    def render_film(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        plan_data = json.loads((workspace / "film_plan.json").read_text(encoding="utf-8"))
        plan = _plan_from_json(plan_data)
        result = adapter.run(goal, workspace)
        qc = validate_cinematic_result(result, plan, workspace)
        if qc.get("status") == "approved":
            regen = workspace / "regeneration_request.json"
            if regen.exists():
                regen.unlink()
        merged = dict(result)
        merged["cinematic_qc"] = qc
        return merged

    def video_qc(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        return validate_video_result(context["render_film"], workspace)

    def upload_qc(context: dict[str, Any], workspace: Path) -> dict[str, Any]:
        result = context["render_film"]
        if not (result.get("video_id") or result.get("youtube_video_id")):
            raise RuntimeError("adapter must upload the video and return video_id")
        return validate_upload_result(result)

    job = pipeline.run(
        goal,
        [
            Stage("develop_film", develop_film, retries=2),
            Stage("render_film", render_film, retries=3),
            Stage("video_qc", video_qc, retries=1),
            Stage("upload_qc", upload_qc, retries=1),
        ],
    )
    return {
        "status": job.status,
        "job_id": job.job_id,
        "goal": job.goal,
        "film": job.stages.get("develop_film").output if "develop_film" in job.stages else {},
        "stages": {name: state.output for name, state in job.stages.items()},
    }


def _plan_from_json(data: dict[str, Any]) -> FilmPlan:
    """Rehydrate the persisted plan without requiring the original LLM call."""
    return CinematicPlanner._from_dict(data, str(data.get("title", "film")))
