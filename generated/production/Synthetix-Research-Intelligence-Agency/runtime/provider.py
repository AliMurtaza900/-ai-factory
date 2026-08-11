"""Standalone provider client for generated agents."""

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
_MAX_RETRIES = 2


def _mock(prompt: str, reason: str = "deterministic offline mode") -> Response:
    lower = prompt.lower()
    if "reviewer" in lower:
        text = "Offline final review result: the pipeline completed successfully; live-provider and evidence caveats are retained."
    elif "risk" in lower:
        text = "Offline risk assessment result: provider availability and evidence quality require live verification."
    elif "market" in lower or "financial" in lower:
        text = "Offline market analysis result: financial and market conclusions require live evidence; this fallback confirms pipeline execution."
    elif "verif" in lower:
        text = "Offline verification result: supplied evidence was structurally checked; live factual verification requires an available provider."
    elif "research" in lower:
        text = "Offline research result: live-source evidence requires an available provider and should be verified before production use."
    elif "writer" in lower or "executive" in lower:
        text = "Offline executive report result: the report pipeline completed; live evidence is required for factual conclusions."
    else:
        text = "Offline generated response: the standalone system completed its requested pipeline without a live provider."
    return Response("offline", "deterministic-fallback", f"{text} ({reason})")


def _enabled(value: str | None) -> bool:
    return (value or "").lower() in {"1", "true", "yes", "on"}


def _provider_order() -> list[str]:
    configured = ["gemini", "groq", "github-models", "openai", "cerebras", "openrouter"]
    preferred = os.getenv("AI_FACTORY_PROVIDER", "").strip().lower()
    aliases = {"github": "github-models", "github_models": "github-models", "githubmodels": "github-models"}
    preferred = aliases.get(preferred, preferred)
    if preferred in configured:
        return [preferred] + [name for name in configured if name != preferred]
    return configured


def generate(prompt: str) -> Response:
    """Generate text through the configured provider chain with deterministic fallback."""
    if _enabled(os.getenv("AI_FACTORY_MOCK")):
        return _mock(prompt)

    keys = {
        "gemini": os.getenv("AI_FACTORY_GEMINI_KEY") or os.getenv("AI_FACTORY_API_KEY"),
        "groq": os.getenv("AI_FACTORY_GROQ_KEY"),
        "github-models": os.getenv("AI_FACTORY_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN"),
        "openai": os.getenv("AI_FACTORY_OPENAI_KEY"),
        "cerebras": os.getenv("AI_FACTORY_CEREBRAS_KEY"),
        "openrouter": os.getenv("AI_FACTORY_OPENROUTER_KEY"),
    }
    models = {
        "gemini": os.getenv("AI_FACTORY_GEMINI_MODEL") or os.getenv("AI_FACTORY_MODEL"),
        "groq": os.getenv("AI_FACTORY_GROQ_MODEL") or "llama-3.1-8b-instant",
        "github-models": os.getenv("AI_FACTORY_GITHUB_MODEL") or "openai/gpt-4.1-mini",
        "openai": os.getenv("AI_FACTORY_OPENAI_MODEL") or "gpt-5.6",
        "cerebras": os.getenv("AI_FACTORY_CEREBRAS_MODEL") or "llama-3.1-8b",
        "openrouter": os.getenv("AI_FACTORY_OPENROUTER_MODEL"),
    }
    errors = []
    for provider in _provider_order():
        key, model = keys[provider], models[provider]
        if not key or not model:
            continue
        try:
            if provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                body = {"contents": [{"parts": [{"text": prompt}]}]}
                headers = {}
            else:
                urls = {
                    "groq": "https://api.groq.com/openai/v1/chat/completions",
                    "github-models": "https://models.github.ai/inference/chat/completions",
                    "openai": "https://api.openai.com/v1/chat/completions",
                    "cerebras": "https://api.cerebras.ai/v1/chat/completions",
                    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
                }
                url = urls[provider]
                body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
                headers = {"Authorization": f"Bearer {key}"}
            data = _post(url, body, headers)
            if provider == "gemini":
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                text = data["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("provider returned an empty response")
            return Response(provider, model, text)
        except Exception as exc:
            errors.append(f"{provider}: {exc}")

    if _enabled(os.getenv("AI_FACTORY_STRICT_PROVIDER")):
        raise RuntimeError("No standalone AI provider succeeded: " + (" | ".join(errors) or "no provider credentials configured"))
    reason = "provider outage; " + " | ".join(errors) if errors else "no provider credentials configured"
    return _mock(prompt, reason)


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
                delay = min(float(retry_after), 15.0) if retry_after else 2 ** attempt
            except (TypeError, ValueError):
                delay = 2 ** attempt
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt >= _MAX_RETRIES:
                raise
            time.sleep(2 ** attempt)
    raise last_error or RuntimeError("Provider request failed without an error")
