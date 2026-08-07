"""Construct the configured model provider without exposing credentials."""

import os

from .base import ModelProvider
from .cached import CachedProvider
from .gemini import GeminiProvider
from .openai_compatible import OpenAICompatibleProvider


def configured_provider() -> ModelProvider:
    """Return the configured provider, or fail clearly when none is configured."""
    provider = os.getenv("AI_FACTORY_PROVIDER", "openai-compatible").strip().lower()
    if provider in {"gemini", "google", "google-gemini"}:
        return CachedProvider(GeminiProvider())
    if provider == "openai-compatible":
        return CachedProvider(OpenAICompatibleProvider())
    raise ValueError(f"Unsupported AI_FACTORY_PROVIDER: {provider}")
