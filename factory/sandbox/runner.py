"""Sandbox execution interface.

The factory deliberately does not provide a fake security boundary. Production
execution must be supplied by an isolated runtime such as a container, VM, or
other hardened sandbox with OS-level resource and network controls.
"""

from dataclasses import dataclass
from typing import Protocol

from .policy import SandboxPolicy


@dataclass(frozen=True)
class ExecutionResult:
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


class SandboxRunner(Protocol):
    """Contract implemented by a real isolated execution backend."""

    def run(self, command: list[str], *, policy: SandboxPolicy) -> ExecutionResult:
        """Run an approved command inside an isolated environment."""
        ...


class UnconfiguredSandbox:
    """Fail closed until a real isolated backend is configured."""

    def run(self, command: list[str], *, policy: SandboxPolicy) -> ExecutionResult:
        raise RuntimeError(
            "No sandbox backend configured. Generated code must not run directly on the host."
        )
