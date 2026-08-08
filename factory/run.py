"""Single-command end-to-end Factory workflow."""

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .autonomous import AutonomousFactory
from .builder.project import AgentProjectBuilder
from .learning.pattern_store import PatternStore, SuccessfulPattern
from .multi_agent.team import AgentTeam, TeamMember


@dataclass(frozen=True)
class ProductionResult:
    goal: str
    passed: bool
    attempts: int
    output_dir: Path
    reused_patterns: int


def _is_complex_multi_agent_goal(goal: str) -> bool:
    text = goal.lower()
    markers = ("multi-agent", "multiple agents", "agent team", "researches", "verifies", "financial", "market analysis", "risks", "final reviewer")
    return sum(marker in text for marker in markers) >= 3


def _build_multi_agent_team(goal: str) -> AgentTeam:
    return AgentTeam(
        goal=goal,
        members=[
            TeamMember("researcher", "research", "Research the business question using multiple relevant sources.", ["business_question"], ["research_evidence"]),
            TeamMember("verifier", "verification", "Verify, compare, and qualify the research evidence.", ["research_evidence"], ["verified_evidence"]),
            TeamMember("market_analyst", "financial and market analysis", "Perform financial and market analysis from verified evidence.", ["verified_evidence"], ["market_analysis"]),
            TeamMember("risk_analyst", "risk analysis", "Identify material risks, uncertainties, assumptions, and missing evidence.", ["verified_evidence", "market_analysis"], ["risk_assessment"]),
            TeamMember("writer", "executive writer", "Produce a clear executive report from the team's evidence and analysis.", ["verified_evidence", "market_analysis", "risk_assessment"], ["executive_report"]),
            TeamMember("reviewer", "final reviewer", "Validate the final report against evidence, analysis, risks, and acceptance criteria.", ["executive_report", "risk_assessment"], ["reviewed_report"]),
        ],
    )


def _materialize_team(team: AgentTeam, output_dir: Path) -> None:
    errors = team.validate()
    if errors:
        raise ValueError("Invalid generated team: " + "; ".join(errors))

    output_dir.mkdir(parents=True, exist_ok=True)
    builder = AgentProjectBuilder()
    for spec in team.agent_specs():
        for generated in builder.build(spec):
            path = output_dir / generated.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(generated.content, encoding="utf-8")

    (output_dir / "team.json").write_text(json.dumps({
        "goal": team.goal,
        "members": [member.__dict__ for member in team.members],
        "plan": team.plan(),
        "validation": "passed",
    }, indent=2) + "\n", encoding="utf-8")


def run_factory(goal: str, *, output_root: str | Path = "generated", max_attempts: int = 2) -> ProductionResult:
    if not goal or not goal.strip():
        raise ValueError("A non-empty goal is required")

    goal = goal.strip()
    store = PatternStore()
    reused = len(store.relevant(goal))
    result = AutonomousFactory().run(goal, max_attempts=max_attempts)

    safe_name = result.design.spec.name.strip() or "generated-agent"
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", safe_name).strip("-") or "generated-agent"
    output_dir = Path(output_root) / safe_name

    if _is_complex_multi_agent_goal(goal):
        team = _build_multi_agent_team(goal)
        _materialize_team(team, output_dir)
        (output_dir / "SPEC.json").write_text(json.dumps({
            "type": "multi-agent-team",
            "name": safe_name,
            "purpose": goal,
            "members": [member.__dict__ for member in team.members],
        }, indent=2) + "\n", encoding="utf-8")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        for generated in result.design.files:
            path = output_dir / generated.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(generated.content, encoding="utf-8")
        (output_dir / "SPEC.json").write_text(
            json.dumps(result.design.spec.to_dict(), indent=2), encoding="utf-8"
        )

    if result.passed:
        store.record(SuccessfulPattern(
            goal=goal,
            agent_name=safe_name,
            capabilities=result.design.spec.capabilities,
            acceptance_criteria=result.design.spec.acceptance_criteria,
        ))

    return ProductionResult(goal, result.passed, result.attempts, output_dir, reused)
