import json
import os
import tempfile
import unittest
from pathlib import Path

from factory.production.cinematic import CinematicPlanner, validate_cinematic_result


class CinematicPipelineTests(unittest.TestCase):
    def test_deterministic_plan_is_complete(self):
        previous = os.environ.get("AI_FACTORY_ENABLE_LLM_CINEMATIC")
        os.environ["AI_FACTORY_ENABLE_LLM_CINEMATIC"] = "0"
        try:
            plan = CinematicPlanner().plan("a lost toy finds its way home")
        finally:
            if previous is None:
                os.environ.pop("AI_FACTORY_ENABLE_LLM_CINEMATIC", None)
            else:
                os.environ["AI_FACTORY_ENABLE_LLM_CINEMATIC"] = previous

        self.assertGreaterEqual(len(plan.shots), 7)
        self.assertTrue(plan.characters)
        self.assertTrue(plan.locations)
        self.assertEqual(len({shot.id for shot in plan.shots}), len(plan.shots))

    def test_failed_shot_creates_targeted_regeneration_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = CinematicPlanner()._deterministic_plan("test")
            result = {
                "status": "completed",
                "video": "video.mp4",
                "shots": [
                    {
                        "id": plan.shots[0].id,
                        "quality": {key: 95 for key in ("character_consistency", "animation", "facial_expression", "cinematography", "lighting", "environment", "continuity", "audio_sync")},
                        "continuity_ok": True,
                    },
                    {
                        "id": plan.shots[1].id,
                        "quality": {"character_consistency": 40},
                        "continuity_ok": False,
                    },
                ],
            }
            with self.assertRaises(RuntimeError):
                validate_cinematic_result(result, plan, root)
            request = json.loads((root / "regeneration_request.json").read_text(encoding="utf-8"))
            self.assertEqual(request["status"], "regenerate")
            self.assertTrue(any(item["id"] == plan.shots[1].id for item in request["failed_shots"]))

    def test_all_good_shots_are_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = CinematicPlanner()._deterministic_plan("test")
            scores = {key: 90 for key in ("character_consistency", "animation", "facial_expression", "cinematography", "lighting", "environment", "continuity", "audio_sync")}
            result = {"status": "completed", "shots": [{"id": shot.id, "quality": scores, "continuity_ok": True} for shot in plan.shots]}
            approved = validate_cinematic_result(result, plan, root)
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(approved["shots"], len(plan.shots))


if __name__ == "__main__":
    unittest.main()
