"""Availability-aware fallback provider chain."""

from .base import ModelProvider, ModelResponse


class FallbackProvider(ModelProvider):
    name = "fallback"

    def __init__(self, providers: list[ModelProvider]):
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider")
        self.providers = list(providers)

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = provider.generate(prompt, system=system)
                if not result.text or not result.text.strip():
                    raise RuntimeError("provider returned an empty response")
                print(f"provider: {provider.name} available -> success")
                return result
            except Exception as exc:
                message = str(exc).replace("\n", " ")[:2000]
                errors.append(f"{provider.name}: {message}")
                print(f"provider: {provider.name} unavailable -> skip: {message}")
        raise RuntimeError("All configured AI providers failed: " + " | ".join(errors))
