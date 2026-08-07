"""Google Gemini provider using the Gemini generateContent REST API."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .base import ModelProvider, ModelResponse


class GeminiProvider(ModelProvider):
    name = "gemini"

    def __init__(self, api_key=None, model=None, timeout=60):
        self.api_key = api_key or os.getenv("AI_FACTORY_API_KEY")
        self.model = model or os.getenv("AI_FACTORY_MODEL")
        self.timeout = timeout

    @staticmethod
    def _normalize_model(value: str) -> str:
        model = value.strip()
        if model.startswith("http"):
            model = model.rstrip("/").split("/models/")[-1]
        model = model.removeprefix("models/")
        if model.endswith(":generateContent"):
            model = model[: -len(":generateContent")]
        return model.strip("/")

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("AI_FACTORY_API_KEY is not configured")
        if not self.model:
            raise RuntimeError("AI_FACTORY_MODEL is not configured")

        model = self._normalize_model(self.model)
        if not model or "/" in model:
            raise RuntimeError("AI_FACTORY_MODEL must be a Gemini model name such as gemini-2.5-flash")

        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload_obj = {"contents": contents}
        if system:
            payload_obj["systemInstruction"] = {"parts": [{"text": system}]}
        payload = json.dumps(payload_obj).encode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent"
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini HTTP {exc.code}: {body[:2000]}") from exc
        except Exception as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Gemini returned an unexpected response: {json.dumps(data)[:2000]}") from exc
        return ModelResponse(text=text, provider=self.name, model=model)
