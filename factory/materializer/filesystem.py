"""Safe local materialization of generated agent files."""

from pathlib import Path

from ..builder.manifest import validate_paths
from ..builder.project import GeneratedFile


class FileSystemMaterializer:
    """Write generated files below one explicit workspace directory."""

    def materialize(self, workspace: str | Path, files: list[GeneratedFile]) -> list[Path]:
        validate_paths(files)
        root = Path(workspace).resolve()
        root.mkdir(parents=True, exist_ok=True)
        written: list[Path] = []
        for generated in files:
            target = (root / generated.path).resolve()
            if root != target and root not in target.parents:
                raise ValueError(f"Generated file escaped workspace: {generated.path}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(generated.content, encoding="utf-8")
            written.append(target)
        return written
