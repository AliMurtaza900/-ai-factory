"""Small in-process cache for provider calls within one Factory run."""

from .base import ModelProvider, ModelResponse


class CachedProvider(ModelProvider):
    """Return the same response for identical requests without another API call."""

    def __init__(self, provider: ModelProvider):
        self.provider = provider
        self._cache: dict[tuple[str, str | None], ModelResponse] = {}

    @property
    def name(self) -> str:
        return self.provider.name

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        key = (prompt, system)
        if key not in self._cache:
            self._cache[key] = self.provider.generate(prompt, system=system)
        return self._cache[key]
