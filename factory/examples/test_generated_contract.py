import os
import sys
import tempfile
import unittest
from pathlib import Path

from factory.run import _build_multi_agent_team, _materialize_team


EXPECTED_ORDER = ["researcher", "verifier", "market_analyst", "risk_analyst", "writer", "reviewer"]


class GeneratedContractTests(unittest.TestCase):
    def test_multi_agent_team_materializes_and_runs_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            team = _build_multi_agent_team("Create a multi-agent AI research company")
            _materialize_team(team, root)
            self.assertEqual(team.validate(), [])
            self.assertTrue((root / "run.py").is_file())
            self.assertTrue((root / "team.json").is_file())
            self.assertTrue((root / "runtime/provider.py").is_file())
            self.assertTrue((root / "requirements.txt").is_file())
            old_mock = os.environ.get("AI_FACTORY_MOCK")
            old_run = sys.modules.pop("run", None)
            os.environ["AI_FACTORY_MOCK"] = "1"
            sys.path.insert(0, str(root))
            try:
                import run as generated_run
                result = generated_run.run("Should a company expand into a new market?")
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["agents"], EXPECTED_ORDER)
                self.assertEqual(list(result["outputs"]), EXPECTED_ORDER)
                self.assertIsInstance(result["final_report"], dict)
                self.assertEqual(result["final_report"], result["outputs"]["reviewer"])
                self.assertEqual(result["final_report"]["agent"], "reviewer")
                self.assertTrue(result["final_report"]["response"])
            finally:
                sys.modules.pop("run", None)
                if old_run is not None:
                    sys.modules["run"] = old_run
                if str(root) in sys.path:
                    sys.path.remove(str(root))
                if old_mock is None:
                    os.environ.pop("AI_FACTORY_MOCK", None)
                else:
                    os.environ["AI_FACTORY_MOCK"] = old_mock

    def test_team_rejects_broken_handoff(self):
        team = _build_multi_agent_team("Create a multi-agent AI research company")
        broken = team.members.copy()
        broken[1] = type(broken[1])(broken[1].name, broken[1].role, broken[1].purpose, ["missing_data"], broken[1].outputs)
        team.members = broken
        self.assertTrue(any("missing upstream inputs" in error for error in team.validate()))


if __name__ == "__main__":
    unittest.main()
