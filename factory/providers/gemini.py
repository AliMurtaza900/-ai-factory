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

    def _request(self, model: str, prompt: str, system: str | None):
        contents = [{"role": "user", "parts": [{"text": prompt}]}]
        payload_obj = {"contents": contents}
        if system:
            payload_obj["systemInstruction"] = {"parts": [{"text": system}]}
        payload = json.dumps(payload_obj).encode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent"
        request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key}, method="POST")
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _available_models(self):
        url = "https://generativelanguage.googleapis.com/v1beta/models?key=" + urllib.parse.quote(self.api_key, safe="")
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [m.get("name", "").removeprefix("models/") for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]

    def generate(self, prompt: str, *, system: str | None = None) -> ModelResponse:
        if not self.api_key:
            raise RuntimeError("AI_FACTORY_API_KEY is not configured")
        configured = self._normalize_model(self.model or "")
        if configured and "/" in configured:
            raise RuntimeError("AI_FACTORY_MODEL must be a Gemini model name")

        candidates = [configured] if configured else []
        try:
            data = self._request(candidates[0], prompt, system) if candidates else None
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code != 404:
                raise RuntimeError(f"Gemini HTTP {exc.code}: {body[:2000]}") from exc
            try:
                available = self._available_models()
            except Exception as list_exc:
                raise RuntimeError(f"Gemini HTTP 404: {body[:1000]}; could not list available models: {list_exc}") from exc
            candidates = available
            data = None
            for model in candidates:
                try:
                    data = self._request(model, prompt, system)
                    configured = model
                    break
                except urllib.error.HTTPError:
                    continue
            if data is None:
                preview = ", ".join(candidates[:15])
                raise RuntimeError(f"Configured Gemini model was unavailable. Available generateContent models: {preview}") from exc
        except Exception as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Gemini returned an unexpected response: {json.dumps(data)[:2000]}") from exc
        return ModelResponse(text=text, provider=self.name, model=configured)
