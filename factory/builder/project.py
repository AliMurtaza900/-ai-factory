"""Safe project materialization from an AgentSpec."""

from dataclasses import dataclass

from ..specs.agent_spec import AgentSpec


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    content: str


class AgentProjectBuilder:
    """Generate a runnable, standalone Python project for an agent."""

    def build(self, spec: AgentSpec) -> list[GeneratedFile]:
        errors = spec.validate()
        if errors:
            raise ValueError("Invalid AgentSpec: " + "; ".join(errors))

        package = self._package_name(spec.name)
        return [
            GeneratedFile(path=f"agents/{package}/__init__.py", content=f'"""Generated agent: {spec.name}."""\n'),
            GeneratedFile(path="runtime/__init__.py", content='"""Standalone runtime for generated agents."""\n'),
            GeneratedFile(path="runtime/provider.py", content=self._provider_module()),
            GeneratedFile(path=f"agents/{package}/agent.py", content=self._agent_module(spec)),
            GeneratedFile(path=f"agents/{package}/SPEC.json", content=self._spec_json(spec)),
            GeneratedFile(path=f"agents/{package}/README.md", content=self._readme(spec)),
            GeneratedFile(path="requirements.txt", content="urllib3>=2.0\n"),
        ]

    @staticmethod
    def _package_name(name: str) -> str:
        normalized = "".join(ch.lower() if ch.isalnum() else "_" for ch in name)
        normalized = "_".join(part for part in normalized.split("_") if part)
        if not normalized:
            raise ValueError("Agent name must contain at least one alphanumeric character")
        return normalized

    @staticmethod
    def _provider_module() -> str:
        return '''"""Standalone provider client used by generated agents."""

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    provider: str
    model: str
    text: str


def generate(prompt: str) -> Response:
    """Generate text using the first configured provider, without importing Factory."""
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
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode())
'''

    @staticmethod
    def _agent_module(spec: AgentSpec) -> str:
        return f'''"""Generated runtime for {spec.name}."""

from typing import Any

from runtime.provider import generate


class Agent:
    """{spec.purpose}"""

    name = {spec.name!r}
    role = {spec.role!r}

    def run(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Run independently through the generated project's provider client."""
        missing = [key for key in {spec.inputs!r} if key not in inputs]
        if missing:
            raise ValueError(f"Missing required inputs: {{missing}}")
        prompt = (
            f"You are the {{self.role}} agent '{{self.name}}'.\\n"
            f"Purpose: {spec.purpose}\\n"
            f"Requested task inputs: {{inputs!r}}\\n"
            "Return a useful response that satisfies the agent purpose."
        )
        response = generate(prompt)
        return {{"status": "completed", "agent": self.name, "provider": response.provider, "model": response.model, "response": response.text}}
'''

    @staticmethod
    def _spec_json(spec: AgentSpec) -> str:
        import json
        return json.dumps(spec.to_dict(), indent=2, sort_keys=True) + "\n"

    @staticmethod
    def _readme(spec: AgentSpec) -> str:
        criteria = "\n".join(f"- {item}" for item in spec.acceptance_criteria)
        return f"""# {spec.name}\n\n{spec.purpose}\n\n**Role:** `{spec.role}`\n\n## Acceptance criteria\n\n{criteria}\n\nThis project was generated by AI Factory and includes its own standalone provider runtime. It does not import the Factory package.\n"""
