"""Provider abstraction used by planner/builder agents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResponse:
    text: str
    provider: str
    model: str


class ModelProvider(ABC):
    """Small interface so the factory is not locked to one AI vendor."""

    name: str

    @abstractmethod
    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        """Generate text from a prompt."""
        raise NotImplementedError
