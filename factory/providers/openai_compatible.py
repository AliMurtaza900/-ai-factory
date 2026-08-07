"""OpenAI-compatible model provider using only the Python standard library."""

import json
import os
import urllib.error
import urllib.request

from .base import ModelProvider, ModelResponse


class OpenAICompatibleProvider(ModelProvider):
    """Provider for OpenAI-compatible chat-completions APIs."""

    name = "openai-compatible"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("AI_FACTORY_API_KEY")
        self.model = model or os.getenv("AI_FACTORY_MODEL")
        self.base_url = (base_url or os.getenv("AI_FACTORY_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("AI_FACTORY_API_KEY is not configured")
        if not self.model:
            raise RuntimeError("AI_FACTORY_MODEL is not configured")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({"model": self.model, "messages": messages}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = exc.read().decode("utf-8", errors="replace")[:2000]
            except Exception:
                body = "<unable to read provider response>"
            raise RuntimeError(f"Model provider HTTP {exc.code}: {body}") from exc
        except Exception as exc:
            raise RuntimeError(f"Model provider request failed: {exc}") from exc

        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Model provider returned an unexpected response") from exc
        return ModelResponse(text=text, provider=self.name, model=self.model)
