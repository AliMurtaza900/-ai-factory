"""Resumable production pipeline with retries, parallel stages, and QC gates."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
from pathlib import Path
import threading
import time
from typing import Any, Callable, Iterable

from .job import JobState, JobStore

StageFn = Callable[[dict[str, Any], Path], dict[str, Any]]


@dataclass(frozen=True)
class Stage:
    name: str
    run: StageFn
    retries: int = 2
    parallel_group: str | None = None


class ProductionPipeline:
    """Execute stages exactly once when possible and resume safely after failure."""

    def __init__(self, store: JobStore | None = None, workspace_root: str | Path = "data/workspaces") -> None:
        self.store = store or JobStore()
        self.workspace_root = Path(workspace_root)
        self._lock = threading.RLock()

    @staticmethod
    def job_id(goal: str) -> str:
        digest = hashlib.sha256(goal.strip().encode("utf-8")).hexdigest()[:16]
        return f"job-{digest}"

    def run(
        self,
        goal: str,
        stages: Iterable[Stage],
        metadata: dict[str, Any] | None = None,
        job_id: str | None = None,
    ) -> JobState:
        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("goal must be non-empty")
        stages = list(stages)
        resolved_job_id = job_id or self.job_id(goal)
        try:
            job = self.store.load(resolved_job_id)
        except FileNotFoundError:
            job = JobState(job_id=resolved_job_id, goal=goal.strip(), metadata=metadata or {})
            self.store.save(job)
        if job.goal != goal.strip():
            raise ValueError(f"job {resolved_job_id} already belongs to a different goal")
        workspace = self.workspace_root / resolved_job_id
        context: dict[str, Any] = dict(job.metadata)
        for state in job.stages.values():
            if state.status == "completed":
                context[state.name] = state.output
        job.status = "running"
        self.store.save(job)

        index = 0
        while index < len(stages):
            current = stages[index]
            if current.parallel_group:
                group: list[Stage] = []
                group_name = current.parallel_group
                while index < len(stages) and stages[index].parallel_group == group_name:
                    group.append(stages[index])
                    index += 1
                self._run_parallel(job, context, workspace, group)
            else:
                self._run_stage(job, context, workspace, current)
                index += 1

        job.status = "completed"
        self.store.save(job)
        return job

    def _save(self, job: JobState) -> None:
        with self._lock:
            self.store.save(job)

    def _run_parallel(self, job: JobState, context: dict[str, Any], workspace: Path, stages: list[Stage]) -> None:
        with ThreadPoolExecutor(max_workers=len(stages)) as pool:
            futures = [pool.submit(self._run_stage, job, context, workspace, stage) for stage in stages]
            for future in futures:
                future.result()

    def _run_stage(self, job: JobState, context: dict[str, Any], workspace: Path, stage: Stage) -> None:
        with self._lock:
            state = job.stage(stage.name)
            if state.status == "completed":
                return
        workspace.mkdir(parents=True, exist_ok=True)
        last_error: Exception | None = None
        for attempt in range(1, stage.retries + 2):
            with self._lock:
                state = job.stage(stage.name)
                state.status = "running"
                state.attempts = attempt
                state.started_at = state.started_at or job.updated_at
                state.error = None
                self.store.save(job)
            try:
                output = stage.run(dict(context), workspace)
                if not isinstance(output, dict):
                    raise RuntimeError(f"stage {stage.name} must return a dict")
                with self._lock:
                    state.output = output
                    state.status = "completed"
                    context[stage.name] = output
                    self.store.save(job)
                return
            except Exception as exc:
                last_error = exc
                with self._lock:
                    state.error = str(exc)[:4000]
                    state.status = "retrying" if attempt <= stage.retries else "failed"
                    self.store.save(job)
                if attempt <= stage.retries:
                    time.sleep(min(2 ** (attempt - 1), 8))
        with self._lock:
            job.status = "failed"
            self.store.save(job)
        raise RuntimeError(f"stage {stage.name} failed after {stage.retries + 1} attempts: {last_error}")
