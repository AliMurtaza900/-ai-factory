"""Resilient provider chain with bounded transient-error retries."""

import os
import time

from .base import ModelProvider, ModelResponse


_TRANSIENT_MARKERS = (
    "429", "408", "500", "502", "503", "504",
    "rate limit", "too many requests", "temporarily unavailable",
    "timed out", "timeout", "connection reset", "connection aborted",
    "service unavailable", "gateway timeout",
)


class FallbackProvider(ModelProvider):
    name = "fallback"

    def __init__(self, providers: list[ModelProvider]):
        if not providers:
            raise ValueError("FallbackProvider requires at least one provider")
        self.providers = list(providers)
        self.retry_attempts = max(0, int(os.getenv("AI_FACTORY_PROVIDER_RETRIES", "2")))
        self.retry_base_delay = max(0.0, float(os.getenv("AI_FACTORY_PROVIDER_RETRY_DELAY", "1")))

    @staticmethod
    def _is_transient(exc: Exception) -> bool:
        text = str(exc).lower()
        return any(marker in text for marker in _TRANSIENT_MARKERS)

    def _generate(self, provider: ModelProvider, prompt: str, system: str | None) -> ModelResponse:
        for attempt in range(self.retry_attempts + 1):
            try:
                result = provider.generate(prompt, system=system)
                if not result.text or not result.text.strip():
                    raise RuntimeError("provider returned an empty response")
                return result
            except Exception as exc:
                if attempt >= self.retry_attempts or not self._is_transient(exc):
                    raise
                delay = self.retry_base_delay * (2 ** attempt)
                print(f"provider: {provider.name} transient failure; retry {attempt + 1}/{self.retry_attempts} in {delay:g}s")
                if delay:
                    time.sleep(delay)
        raise RuntimeError("unreachable")

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        errors: list[str] = []
        for provider in self.providers:
            try:
                result = self._generate(provider, prompt, system)
                print(f"provider: {provider.name} available -> success")
                return result
            except Exception as exc:
                message = str(exc).replace("\n", " ")[:2000]
                errors.append(f"{provider.name}: {message}")
                print(f"provider: {provider.name} unavailable -> skip: {message}")
        raise RuntimeError("All configured AI providers failed: " + " | ".join(errors))
