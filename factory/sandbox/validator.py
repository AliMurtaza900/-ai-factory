"""Validation before generated projects are handed to a sandbox."""

from pathlib import PurePosixPath

from ..builder.project import GeneratedFile


BLOCKED_FILENAMES = {".env", ".gitconfig", "id_rsa", "id_ed25519"}


def validate_generated_project(files: list[GeneratedFile]) -> None:
    """Reject path traversal and a few high-risk credential/config filenames."""
    for generated in files:
        path = PurePosixPath(generated.path)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Unsafe generated path: {generated.path}")
        if path.name in BLOCKED_FILENAMES:
            raise ValueError(f"Blocked generated filename: {path.name}")
