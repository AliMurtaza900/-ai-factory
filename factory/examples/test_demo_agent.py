import unittest

from factory.evaluation.models import TestCase
from factory.evaluation.runner import EvaluationRunner
from factory.examples.demo_agent import run


class DemoAgentTest(unittest.TestCase):
    def test_demo_agent(self) -> None:
        report = EvaluationRunner().run(
            "demo-agent",
            run,
            [TestCase(name="basic", inputs={"question": "hello"}, expected={"answer": "received: hello"})],
        )
        self.assertTrue(report.passed)


if __name__ == "__main__":
    unittest.main()
