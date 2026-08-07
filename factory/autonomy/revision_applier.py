"""Apply explicitly supplied revisions to a generated workspace."""

from pathlib import Path

from ..builder.project import GeneratedFile
from ..builder.manifest import validate_paths


class RevisionApplier:
    """Apply a complete reviewed file set; never accepts arbitrary paths."""

    def apply(self, workspace: str | Path, files: list[GeneratedFile]) -> list[Path]:
        validate_paths(files)
        root = Path(workspace).resolve()
        root.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for item in files:
            target = (root / item.path).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"Revision escaped workspace: {item.path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(item.content, encoding="utf-8")
            written.append(target)
        return written
