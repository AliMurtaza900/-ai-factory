"""Availability-aware fallback provider chain."""

from .base import ModelProvider, ModelResponse


class FallbackProvider(ModelProvider):
    name = "fallback"

    def __init__(self, providers: list[ModelProvider]):
        self.providers = providers

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = provider.generate(prompt, system=system)
                print(f"provider: {provider.name} available -> success")
                return result
            except Exception as exc:
                message = str(exc).replace("\n", " ")
                errors.append(f"{provider.name}: {message}")
                print(f"provider: {provider.name} unavailable -> skip: {message}")
        raise RuntimeError("All configured AI providers failed: " + " | ".join(errors))
