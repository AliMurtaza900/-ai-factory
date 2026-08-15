"""Adapter contract for integrating an existing video generator/uploader."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any, Protocol


class VideoAdapter(Protocol):
    def run(self, goal: str, workspace: Path) -> dict[str, Any]: ...


@dataclass
class CommandVideoAdapter:
    """Run an existing video system through a stable JSON contract.

    The command receives GOAL, WORKSPACE and JOB_ID environment variables and
    must print a JSON object. This avoids coupling the Factory to one vendor or
    one user's existing video stack.
    """

    command: str | None = None
    timeout_seconds: int = 3600

    @classmethod
    def from_environment(cls) -> "CommandVideoAdapter":
        timeout = int(os.getenv("AI_FACTORY_VIDEO_TIMEOUT", "3600"))
        return cls(os.getenv("AI_FACTORY_VIDEO_COMMAND"), timeout)

    def run(self, goal: str, workspace: Path) -> dict[str, Any]:
        if not self.command:
            raise RuntimeError(
                "AI_FACTORY_VIDEO_COMMAND is not configured; set it to the existing video generator/uploader command"
            )
        workspace.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update({"GOAL": goal, "WORKSPACE": str(workspace)})
        job_id_file = workspace / "job_id.txt"
        if job_id_file.exists():
            env["JOB_ID"] = job_id_file.read_text(encoding="utf-8").strip()
        completed = subprocess.run(
            shlex.split(self.command),
            cwd=workspace,
            env=env,
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"video command failed with exit code {completed.returncode}: {completed.stderr[-4000:]}"
            )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("video command must emit a JSON result on stdout") from exc
        if not isinstance(result, dict) or result.get("status") != "completed":
            raise RuntimeError(f"video command returned an invalid result: {result!r}")
        return result
