import os
import tempfile
import unittest
from pathlib import Path

from factory.run import _build_multi_agent_team, _materialize_team


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
            old = os.environ.get("AI_FACTORY_MOCK")
            os.environ["AI_FACTORY_MOCK"] = "1"
            try:
                import sys
                sys.path.insert(0, str(root))
                import run as generated_run
                result = generated_run.run("Should a company expand into a new market?")
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["agents"], ["researcher", "verifier", "market_analyst", "risk_analyst", "writer", "reviewer"])
                self.assertIsInstance(result["final_report"], dict)
                self.assertTrue(result["final_report"]["response"])
            finally:
                if old is None:
                    os.environ.pop("AI_FACTORY_MOCK", None)
                else:
                    os.environ["AI_FACTORY_MOCK"] = old
                if str(root) in sys.path:
                    sys.path.remove(str(root))

    def test_team_rejects_broken_handoff(self):
        team = _build_multi_agent_team("Create a multi-agent AI research company")
        broken = team.members.copy()
        broken[1] = type(broken[1])(broken[1].name, broken[1].role, broken[1].purpose, ["missing_data"], broken[1].outputs)
        team.members = broken
        self.assertTrue(any("missing upstream inputs" in error for error in team.validate()))


if __name__ == "__main__":
    unittest.main()
