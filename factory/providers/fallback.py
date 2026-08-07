"""Try configured AI providers in order, skipping unconfigured providers."""

from .base import ModelProvider, ModelResponse


class FallbackProvider(ModelProvider):
    name = "fallback"

    def __init__(self, providers: list[ModelProvider]):
        self.providers = providers

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        errors = []
        for provider in self.providers:
            try:
                return provider.generate(prompt, system=system)
            except Exception as exc:
                errors.append(f"{provider.name}: {exc}")
        raise RuntimeError("All configured AI providers failed: " + " | ".join(errors))
