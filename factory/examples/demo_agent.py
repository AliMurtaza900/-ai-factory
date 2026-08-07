"""End-to-end smoke-test agent used by CI."""

from typing import Any


def run(inputs: dict[str, Any]) -> dict[str, Any]:
    question = inputs.get("question")
    if not question:
        raise ValueError("question is required")
    return {"answer": f"received: {question}"}
