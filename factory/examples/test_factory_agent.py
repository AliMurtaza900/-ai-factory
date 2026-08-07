import unittest

from factory.agents.factory_agent import FactoryAgent


class FactoryAgentTest(unittest.TestCase):
    def test_factory_can_design_and_scaffold(self) -> None:
        result = FactoryAgent().design_and_scaffold("Create a simple research assistant")
        self.assertTrue(result.spec.name)
        self.assertTrue(result.files)
        self.assertTrue(any(file.path.endswith("agent.py") for file in result.files))


if __name__ == "__main__":
    unittest.main()
