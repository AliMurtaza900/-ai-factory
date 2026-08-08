"""Construct configured AI providers with ordered fallback support."""

import os

from .base import ModelProvider
from .cached import CachedProvider
from .fallback import FallbackProvider
from .gemini import GeminiProvider
from .github_models import GitHubModelsProvider
from .groq import GroqProvider
from .cerebras import CerebrasProvider
from .openai_compatible import OpenAICompatibleProvider


def _optional_openai_compatible(prefix: str, default_url: str) -> ModelProvider | None:
    key = os.getenv(f"{prefix}_KEY")
    model = os.getenv(f"{prefix}_MODEL")
    if not key or not model:
        return None
    return OpenAICompatibleProvider(api_key=key, model=model, base_url=os.getenv(f"{prefix}_BASE_URL") or default_url)


def configured_provider() -> ModelProvider:
    """Build the complete configured provider chain; one unavailable vendor never blocks the others."""
    providers: list[ModelProvider] = []
    preferred = os.getenv("AI_FACTORY_PROVIDER", "").strip().lower()

    gemini_key = os.getenv("AI_FACTORY_GEMINI_KEY") or os.getenv("AI_FACTORY_API_KEY")
    gemini_model = os.getenv("AI_FACTORY_GEMINI_MODEL") or os.getenv("AI_FACTORY_MODEL")
    if gemini_key and gemini_model:
        providers.append(GeminiProvider(api_key=gemini_key, model=gemini_model))

    groq_key = os.getenv("AI_FACTORY_GROQ_KEY")
    if groq_key:
        providers.append(GroqProvider(api_key=groq_key, model=os.getenv("AI_FACTORY_GROQ_MODEL") or "llama-3.1-8b-instant"))

    github_token = os.getenv("AI_FACTORY_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if github_token:
        providers.append(GitHubModelsProvider(token=github_token, model=os.getenv("AI_FACTORY_GITHUB_MODEL") or "openai/gpt-4.1-mini"))

    openai_key = os.getenv("AI_FACTORY_OPENAI_KEY")
    if openai_key:
        providers.append(OpenAICompatibleProvider(api_key=openai_key, model=os.getenv("AI_FACTORY_OPENAI_MODEL") or "gpt-5.6", base_url="https://api.openai.com/v1"))

    cerebras_key = os.getenv("AI_FACTORY_CEREBRAS_KEY")
    if cerebras_key:
        providers.append(CerebrasProvider(api_key=cerebras_key, model=os.getenv("AI_FACTORY_CEREBRAS_MODEL") or "llama-3.1-8b"))

    openrouter = _optional_openai_compatible("AI_FACTORY_OPENROUTER", "https://openrouter.ai/api/v1")
    if openrouter:
        providers.append(openrouter)

    if not providers:
        raise RuntimeError("No AI provider configured")

    if preferred:
        matching = [p for p in providers if p.name.lower() == preferred]
        providers = matching + [p for p in providers if p.name.lower() != preferred]

    return CachedProvider(providers[0] if len(providers) == 1 else FallbackProvider(providers))
