import os
import sys
import tempfile
import unittest
from pathlib import Path

from factory.run import CANONICAL_RESEARCH_TEAM_NAME, _build_multi_agent_team, _materialize_team, run_factory


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

    def test_complex_factory_output_has_stable_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_factory(
                "Create a multi-agent AI research company that receives a business question, researches the topic using multiple sources, verifies and compares the evidence, performs financial and market analysis, identifies risks and uncertainties, writes an executive report, and has a final reviewer validate the report before delivery.",
                output_root=tmp,
                max_attempts=1,
            )
            self.assertTrue(result.passed)
            self.assertEqual(result.output_dir.name, CANONICAL_RESEARCH_TEAM_NAME)
            self.assertEqual(result.output_dir.name, "Synthetix-Research-Intelligence-Agency")
            spec = (result.output_dir / "SPEC.json").read_text(encoding="utf-8")
            team = (result.output_dir / "team.json").read_text(encoding="utf-8")
            self.assertIn(CANONICAL_RESEARCH_TEAM_NAME, spec)
            self.assertIn(CANONICAL_RESEARCH_TEAM_NAME, team)


if __name__ == "__main__":
    unittest.main()
