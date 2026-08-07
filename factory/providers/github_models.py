"""GitHub Models provider via the OpenAI-compatible inference endpoint."""

import os

from .openai_compatible import OpenAICompatibleProvider


class GitHubModelsProvider(OpenAICompatibleProvider):
    name = "github-models"

    def __init__(self, token=None, model=None, timeout=60):
        super().__init__(
            api_key=token or os.getenv("AI_FACTORY_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN"),
            model=model or os.getenv("AI_FACTORY_GITHUB_MODEL") or "openai/gpt-4.1-mini",
            base_url="https://models.github.ai/inference",
            timeout=timeout,
        )
