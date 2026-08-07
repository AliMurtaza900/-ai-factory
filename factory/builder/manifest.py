"""Manifest and path-safety helpers for generated agent projects."""

from dataclasses import dataclass
from pathlib import PurePosixPath

from .project import GeneratedFile


@dataclass(frozen=True)
class BuildManifest:
    agent_name: str
    files: tuple[str, ...]


def validate_paths(files: list[GeneratedFile]) -> None:
    """Reject absolute or parent-traversal paths before materialization."""
    for generated in files:
        path = PurePosixPath(generated.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe generated path: {generated.path}")


def make_manifest(agent_name: str, files: list[GeneratedFile]) -> BuildManifest:
    validate_paths(files)
    return BuildManifest(agent_name=agent_name, files=tuple(file.path for file in files))
