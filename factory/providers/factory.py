"""Construct configured AI providers with fallback support."""

import os

from .base import ModelProvider
from .cached import CachedProvider
from .fallback import FallbackProvider
from .gemini import GeminiProvider
from .github_models import GitHubModelsProvider
from .groq import GroqProvider
from .openai_compatible import OpenAICompatibleProvider


def _optional_openai_compatible(prefix: str, default_url: str) -> ModelProvider | None:
    key = os.getenv(f"{prefix}_KEY")
    model = os.getenv(f"{prefix}_MODEL")
    if not key or not model:
        return None
    return OpenAICompatibleProvider(
        api_key=key,
        model=model,
        base_url=os.getenv(f"{prefix}_BASE_URL") or default_url,
    )


def configured_provider() -> ModelProvider:
    """Return provider chain: Gemini -> Groq -> GitHub Models -> OpenAI -> OpenRouter."""
    providers: list[ModelProvider] = []

    gemini_key = os.getenv("AI_FACTORY_GEMINI_KEY") or os.getenv("AI_FACTORY_API_KEY")
    gemini_model = os.getenv("AI_FACTORY_GEMINI_MODEL") or os.getenv("AI_FACTORY_MODEL")
    if gemini_key and gemini_model and os.getenv("AI_FACTORY_PROVIDER", "gemini").lower() == "gemini":
        providers.append(GeminiProvider(api_key=gemini_key, model=gemini_model))

    groq_key = os.getenv("AI_FACTORY_GROQ_KEY")
    groq_model = os.getenv("AI_FACTORY_GROQ_MODEL") or "llama-3.1-8b-instant"
    if groq_key:
        providers.append(GroqProvider(api_key=groq_key, model=groq_model))

    github_token = os.getenv("AI_FACTORY_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    github_model = os.getenv("AI_FACTORY_GITHUB_MODEL") or "openai/gpt-4.1-mini"
    if github_token:
        providers.append(GitHubModelsProvider(token=github_token, model=github_model))

    openai_key = os.getenv("AI_FACTORY_OPENAI_KEY")
    openai_model = os.getenv("AI_FACTORY_OPENAI_MODEL") or "gpt-5.6"
    if openai_key:
        providers.append(OpenAICompatibleProvider(
            api_key=openai_key,
            model=openai_model,
            base_url="https://api.openai.com/v1",
        ))

    openrouter = _optional_openai_compatible("AI_FACTORY_OPENROUTER", "https://openrouter.ai/api/v1")
    if openrouter:
        providers.append(openrouter)

    if not providers and os.getenv("AI_FACTORY_API_KEY"):
        providers.append(OpenAICompatibleProvider())

    if not providers:
        raise RuntimeError("No AI provider configured")
    return CachedProvider(providers[0] if len(providers) == 1 else FallbackProvider(providers))
