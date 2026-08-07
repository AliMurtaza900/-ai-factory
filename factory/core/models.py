"""Shared models used by the AI Factory orchestration layer."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    BUILDING = "building"
    TESTING = "testing"
    IMPROVING = "improving"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FactoryJob:
    """A request for the factory to design or improve an AI system."""

    goal: str
    job_id: str
    status: JobStatus = JobStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class PlanStep:
    """One executable step in an AI-system build plan."""

    name: str
    description: str
    order: int
    agent_role: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
