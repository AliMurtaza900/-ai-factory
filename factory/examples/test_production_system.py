import json
import tempfile
import unittest
from pathlib import Path

from factory.production.analytics import FeedbackStore, VideoMetric
from factory.production.job import JobStore
from factory.production.pipeline import ProductionPipeline, Stage
from factory.production.quality import validate_upload_result, validate_video_result


class ProductionSystemTests(unittest.TestCase):
    def test_retry_and_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = {"n": 0}
            store = JobStore(Path(tmp) / "jobs")
            pipeline = ProductionPipeline(store=store, workspace_root=Path(tmp) / "work")

            def flaky(context, workspace):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise RuntimeError("temporary")
                return {"ok": True}

            job = pipeline.run("retry-me", [Stage("flaky", flaky, retries=1)])
            self.assertEqual(job.status, "completed")
            self.assertEqual(job.stages["flaky"].attempts, 2)

            def should_not_run(context, workspace):
                raise AssertionError("completed stage was executed again")

            resumed = pipeline.run("retry-me", [Stage("flaky", should_not_run, retries=0)])
            self.assertEqual(resumed.status, "completed")

    def test_quality_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "video.mp4"
            video.write_bytes(b"video")
            result = validate_video_result({"status": "completed", "video": str(video), "title": "x"}, root)
            self.assertEqual(result["status"], "approved")
            upload = validate_upload_result({"status": "completed", "video_id": "abc123"})
            self.assertEqual(upload["video_id"], "abc123")

    def test_feedback_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metrics.json"
            store = FeedbackStore(path)
            store.record(VideoMetric("a", views=100, ctr=0.04, retention=0.5))
            store.record(VideoMetric("b", views=200, ctr=0.03, retention=0.4))
            summary = store.summarize()
            self.assertEqual(summary["videos"], 2)
            self.assertEqual(summary["views"], 300)
            self.assertEqual(store.rank()[0].video_id, "b")


if __name__ == "__main__":
    unittest.main()
