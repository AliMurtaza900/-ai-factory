from factory.evaluation.models import TestCase
from factory.evaluation.runner import EvaluationRunner
from factory.examples.demo_agent import run


def test_demo_agent() -> None:
    report = EvaluationRunner().run(
        "demo-agent",
        run,
        [TestCase(name="basic", inputs={"question": "hello"}, expected={"answer": "received: hello"})],
    )
    assert report.passed
