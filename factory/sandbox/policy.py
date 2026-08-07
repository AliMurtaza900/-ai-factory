"""Explicit policy for generated-agent execution."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SandboxPolicy:
    """Conservative defaults for untrusted generated projects."""

    allow_network: bool = False
    allow_process_creation: bool = False
    allow_filesystem_write: bool = False
    timeout_seconds: int = 30
    max_output_bytes: int = 1_000_000
    allowed_environment: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
