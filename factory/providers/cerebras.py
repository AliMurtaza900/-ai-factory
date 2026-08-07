"""Cerebras provider using its OpenAI-compatible API."""

import os

from .openai_compatible import OpenAICompatibleProvider


class CerebrasProvider(OpenAICompatibleProvider):
    name = "cerebras"

    def __init__(self, api_key=None, model=None, timeout=60):
        super().__init__(
            api_key=api_key or os.getenv("AI_FACTORY_CEREBRAS_KEY"),
            model=model or os.getenv("AI_FACTORY_CEREBRAS_MODEL") or "llama-3.1-8b",
            base_url="https://api.cerebras.ai/v1",
            timeout=timeout,
        )
