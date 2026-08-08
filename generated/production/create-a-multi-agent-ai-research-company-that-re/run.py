"""Runnable end-to-end orchestrator for the generated team."""

import argparse
import json

from agents.researcher.agent import Agent as ResearcherAgent
from agents.verifier.agent import Agent as VerifierAgent
from agents.market_analyst.agent import Agent as MarketAnalystAgent
from agents.risk_analyst.agent import Agent as RiskAnalystAgent
from agents.writer.agent import Agent as WriterAgent
from agents.reviewer.agent import Agent as ReviewerAgent

AGENTS = {
    'researcher': ResearcherAgent,
    'verifier': VerifierAgent,
    'market_analyst': MarketAnalystAgent,
    'risk_analyst': RiskAnalystAgent,
    'writer': WriterAgent,
    'reviewer': ReviewerAgent,
}
EXECUTION_ORDER = ['researcher', 'verifier', 'market_analyst', 'risk_analyst', 'writer', 'reviewer']


def run(business_question: str) -> dict:
    if not isinstance(business_question, str) or not business_question.strip():
        raise ValueError("business_question must be a non-empty string")
    outputs = {}

    def execute(name, inputs):
        result = AGENTS[name]().run(inputs)
        if not isinstance(result, dict):
            raise TypeError(f"Agent {name} returned {type(result).__name__}, expected dict")
        if result.get("status") != "completed":
            raise RuntimeError(f"Agent {name} did not complete: {result}")
        if not isinstance(result.get("response"), str) or not result["response"].strip():
            raise RuntimeError(f"Agent {name} returned no response text")
        outputs[name] = result
        return result["response"]

    execute("researcher", {"business_question": business_question})
    execute("verifier", {"research_evidence": outputs["researcher"]["response"]})
    execute("market_analyst", {"verified_evidence": outputs["verifier"]["response"]})
    execute("risk_analyst", {"verified_evidence": outputs["verifier"]["response"], "market_analysis": outputs["market_analyst"]["response"]})
    execute("writer", {"verified_evidence": outputs["verifier"]["response"], "market_analysis": outputs["market_analyst"]["response"], "risk_assessment": outputs["risk_analyst"]["response"]})
    execute("reviewer", {"executive_report": outputs["writer"]["response"], "risk_assessment": outputs["risk_analyst"]["response"]})

    if set(outputs) != set(EXECUTION_ORDER):
        raise RuntimeError("Generated team did not execute every declared agent")
    final_report = outputs["reviewer"]
    return {
        "status": "completed",
        "business_question": business_question,
        "agents": EXECUTION_ORDER.copy(),
        "outputs": outputs,
        "final_report": final_report,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the generated multi-agent system")
    parser.add_argument("question", help="Business/research question")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()
    result = run(args.question)
    print(json.dumps(result, indent=2) if args.json else result["final_report"]["response"])
