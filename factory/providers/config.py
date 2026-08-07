"""Environment-based provider configuration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    api_key: str | None
    model: str | None
    base_url: str

    @classmethod
    def from_environment(cls) -> "ProviderConfig":
        return cls(
            api_key=os.getenv("AI_FACTORY_API_KEY"),
            model=os.getenv("AI_FACTORY_MODEL"),
            base_url=os.getenv("AI_FACTORY_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        )

    def configured(self) -> bool:
        return bool(self.api_key and self.model)
