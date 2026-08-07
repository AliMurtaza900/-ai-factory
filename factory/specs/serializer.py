"""JSON serialization helpers for agent specifications."""

import json
from typing import Any

from .agent_spec import AgentSpec


def spec_to_json(spec: AgentSpec, *, indent: int = 2) -> str:
    """Serialize a validated-or-unvalidated spec as deterministic JSON."""
    return json.dumps(spec.to_dict(), indent=indent, sort_keys=True)


def spec_from_dict(data: dict[str, Any]) -> AgentSpec:
    """Construct a spec from a plain mapping."""
    return AgentSpec(**data)


def spec_from_json(payload: str) -> AgentSpec:
    """Construct a spec from JSON."""
    return spec_from_dict(json.loads(payload))
