"""Standalone provider client used by generated agents."""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    provider: str
    model: str
    text: str


_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
_MAX_RETRIES = 3


def generate(prompt: str) -> Response:
    """Generate text using configured providers, retrying transient failures."""
    candidates = [
        ("gemini", os.getenv("AI_FACTORY_GEMINI_KEY") or os.getenv("AI_FACTORY_API_KEY"), os.getenv("AI_FACTORY_GEMINI_MODEL") or os.getenv("AI_FACTORY_MODEL")),
        ("openai", os.getenv("AI_FACTORY_OPENAI_KEY"), os.getenv("AI_FACTORY_OPENAI_MODEL")),
        ("cerebras", os.getenv("AI_FACTORY_CEREBRAS_KEY"), os.getenv("AI_FACTORY_CEREBRAS_MODEL")),
        ("openrouter", os.getenv("AI_FACTORY_OPENROUTER_KEY"), os.getenv("AI_FACTORY_OPENROUTER_MODEL")),
    ]
    errors = []
    for provider, key, model in candidates:
        if not key or not model:
            continue
        try:
            if provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                body = {"contents": [{"parts": [{"text": prompt}]}]}
                data = _post(url, body, {})
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                urls = {
                    "openai": "https://api.openai.com/v1/chat/completions",
                    "cerebras": "https://api.cerebras.ai/v1/chat/completions",
                    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
                }
                data = _post(urls[provider], {"model": model, "messages": [{"role": "user", "content": prompt}]}, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
                text = data["choices"][0]["message"]["content"]
            return Response(provider, model, text)
        except Exception as exc:
            errors.append(f"{provider}: {exc}")
    raise RuntimeError("No standalone AI provider succeeded: " + " | ".join(errors))


def _post(url: str, body: dict, headers: dict) -> dict:
    request_body = json.dumps(body).encode()
    last_error = None
    for attempt in range(_MAX_RETRIES + 1):
        request = urllib.request.Request(url, data=request_body, headers={"Content-Type": "application/json", **headers}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in _RETRYABLE_STATUS or attempt >= _MAX_RETRIES:
                raise
            retry_after = exc.headers.get("Retry-After")
            try:
                delay = min(float(retry_after), 30.0) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt >= _MAX_RETRIES:
                raise
            time.sleep(2 ** attempt)
    if last_error:
        raise last_error
    raise RuntimeError("Provider request failed without an error")
