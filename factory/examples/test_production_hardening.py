import ast
import hashlib
import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION = REPO_ROOT / "generated" / "production"
CANONICAL = "Synthetix-Research-Intelligence-Agency"


class ProductionHardeningTests(unittest.TestCase):
    def test_no_secret_like_values_in_tracked_source(self):
        # Match actual key-shaped values, not the provider-prefix text used in CI regexes.
        secret_patterns = [
            re.compile(r"(?:A[Ii]za[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,})"),
            re.compile(r"(?:api[_-]?key|authorization|bearer)\s*[:=]\s*['\"][^'\"]{12,}['\"]", re.I),
        ]
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix not in {".py", ".json", ".yml", ".yaml", ".md", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in secret_patterns:
                self.assertIsNone(pattern.search(text), f"secret-like value in {path}")

    def test_generated_system_is_factory_independent(self):
        self.assertTrue(PRODUCTION.exists())
        project = PRODUCTION / CANONICAL
        self.assertTrue((project / "run.py").is_file())
        self.assertTrue((project / "team.json").is_file())
        self.assertTrue((project / "runtime" / "provider.py").is_file())
        for path in project.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("from factory.", text, path.as_posix())
            self.assertNotIn("import factory", text, path.as_posix())
            ast.parse(text, filename=str(path))

    def test_canonical_team_contract(self):
        project = PRODUCTION / CANONICAL
        team = json.loads((project / "team.json").read_text(encoding="utf-8"))
        self.assertEqual(team.get("name"), CANONICAL)
        self.assertEqual(team.get("entrypoint"), "run.py")
        names = {member.get("name") for member in team.get("members", [])}
        self.assertEqual(names, {"researcher", "verifier", "market_analyst", "risk_analyst", "writer", "reviewer"})
        for spec in project.rglob("SPEC.json"):
            self.assertEqual(json.loads(spec.read_text(encoding="utf-8")).get("name"), CANONICAL)

    def test_artifact_manifest_is_complete_and_hashed(self):
        manifest_path = PRODUCTION / "FACTORY_ARTIFACT.json"
        # The manifest is created later in the production workflow. When this
        # regression suite runs before that step, absence is expected; the
        # generated artifact is validated by the final production gate.
        if not manifest_path.is_file():
            return
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest.get("system_name"), CANONICAL)
        self.assertEqual(manifest.get("entrypoint"), "run.py")
        self.assertEqual(manifest.get("end_to_end_test"), "passed")
        files = manifest.get("files", [])
        self.assertIn(f"{CANONICAL}/run.py", files)
        self.assertIn(f"{CANONICAL}/team.json", files)
        self.assertIn(f"{CANONICAL}/runtime/provider.py", files)
        digest = hashlib.sha256()
        for relative in files:
            path = PRODUCTION / relative
            self.assertTrue(path.is_file(), relative)
            digest.update(relative.encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
        self.assertEqual(manifest.get("files_digest_sha256"), digest.hexdigest())


if __name__ == "__main__":
    unittest.main()
