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


def _orchestrator_module(team: AgentTeam) -> str:
    members = [member.name for member in team.members]
    imports = "\n".join(f"from agents.{name}.agent import Agent as {name.title().replace('_', '')}Agent" for name in members)
    classes = "\n".join(f"    {name!r}: {name.title().replace('_', '')}Agent," for name in members)
    return f'''"""Runnable end-to-end orchestrator for the generated team."""

import argparse
import json

{imports}

AGENTS = {{
{classes}
}}
EXECUTION_ORDER = {members!r}


def run(business_question: str) -> dict:
    if not isinstance(business_question, str) or not business_question.strip():
        raise ValueError("business_question must be a non-empty string")
    outputs = {{}}

    def execute(name, inputs):
        result = AGENTS[name]().run(inputs)
        if not isinstance(result, dict):
            raise TypeError(f"Agent {{name}} returned {{type(result).__name__}}, expected dict")
        if result.get("status") != "completed":
            raise RuntimeError(f"Agent {{name}} did not complete: {{result}}")
        if not isinstance(result.get("response"), str) or not result["response"].strip():
            raise RuntimeError(f"Agent {{name}} returned no response text")
        outputs[name] = result
        return result["response"]

    research = execute("researcher", {{"business_question": business_question}})
    verified = execute("verifier", {{"research_evidence": research}})
    market = execute("market_analyst", {{"verified_evidence": verified}})
    risks = execute("risk_analyst", {{"verified_evidence": verified, "market_analysis": market}})
    report = execute("writer", {{"verified_evidence": verified, "market_analysis": market, "risk_assessment": risks}})
    reviewed = execute("reviewer", {{"executive_report": report, "risk_assessment": risks}})

    return {{
        "status": "completed",
        "business_question": business_question,
        "agents": list(outputs),
        "outputs": outputs,
        "final_report": reviewed,
    }}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the generated multi-agent system")
    parser.add_argument("question", help="Business/research question")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()
    result = run(args.question)
    print(json.dumps(result, indent=2) if args.json else result["final_report"]["response"])
'''


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
    (output_dir / "run.py").write_text(_orchestrator_module(team), encoding="utf-8")
    (output_dir / "team.json").write_text(json.dumps({"goal": team.goal, "members": [member.__dict__ for member in team.members], "plan": team.plan(), "validation": "passed", "entrypoint": "run.py"}, indent=2) + "\n", encoding="utf-8")


def run_factory(goal: str, *, output_root: str | Path = "generated", max_attempts: int = 2) -> ProductionResult:
    if not isinstance(goal, str) or not goal.strip():
        raise ValueError("A non-empty goal is required")
    if not isinstance(max_attempts, int) or max_attempts < 1:
        raise ValueError("max_attempts must be a positive integer")
    goal = goal.strip()
    store = PatternStore()
    reused = len(store.relevant(goal))
    result = AutonomousFactory().run(goal, max_attempts=max_attempts)
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", result.design.spec.name.strip() or "generated-agent").strip("-") or "generated-agent"
    output_dir = Path(output_root) / safe_name
    if _is_complex_multi_agent_goal(goal):
        team = _build_multi_agent_team(goal)
        _materialize_team(team, output_dir)
        (output_dir / "SPEC.json").write_text(json.dumps({"type": "multi-agent-team", "name": safe_name, "purpose": goal, "members": [member.__dict__ for member in team.members], "entrypoint": "run.py"}, indent=2) + "\n", encoding="utf-8")
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
        for generated in result.design.files:
            path = output_dir / generated.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(generated.content, encoding="utf-8")
        (output_dir / "SPEC.json").write_text(json.dumps(result.design.spec.to_dict(), indent=2) + "\n", encoding="utf-8")
    if result.passed:
        store.record(SuccessfulPattern(goal=goal, agent_name=safe_name, capabilities=result.design.spec.capabilities, acceptance_criteria=result.design.spec.acceptance_criteria))
    return ProductionResult(goal, result.passed, result.attempts, output_dir, reused)
