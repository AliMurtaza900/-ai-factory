"""Groq provider using the OpenAI-compatible chat completions API."""

import os

from .openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"

    def __init__(self, api_key=None, model=None, timeout=60):
        super().__init__(
            api_key=api_key or os.getenv("AI_FACTORY_GROQ_KEY"),
            model=model or os.getenv("AI_FACTORY_GROQ_MODEL") or "llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1",
            timeout=timeout,
        )
