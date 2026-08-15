import tempfile
import unittest
from pathlib import Path

from factory.production.analytics import FeedbackStore, VideoMetric
from factory.production.optimizer import ProductionOptimizer
from factory.production.queue import ProductionQueue


class AutonomousProductionTests(unittest.TestCase):
    def test_queue_survives_and_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = ProductionQueue(Path(tmp) / "queue.json")
            item = queue.enqueue("make a test video", {"channel": "test"})
            result = queue.run_next(lambda goal, metadata: {"status": "completed", "job_id": "job-test"})
            self.assertEqual(item.goal, "make a test video")
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.job_id, "job-test")
            self.assertEqual(queue.pending(), [])

    def test_optimizer_is_conservative(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FeedbackStore(Path(tmp) / "metrics.json")
            store.record(VideoMetric("a", views=100, ctr=0.08, retention=0.55))
            store.record(VideoMetric("b", views=50, ctr=0.04, retention=0.35))
            report = ProductionOptimizer(store).recommend()
            self.assertEqual(report["sample_size"], 2)
            self.assertEqual(report["confidence"], "low")
            self.assertTrue(report["recommendations"])


if __name__ == "__main__":
    unittest.main()
