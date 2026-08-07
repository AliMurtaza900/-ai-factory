import unittest

from factory.improvement.patch_gate import PatchGate


class PatchGateTests(unittest.TestCase):
    def test_accepts_bounded_proposals_when_validation_passes(self):
        gate = PatchGate(lambda: True, max_proposals=2)
        decision = gate.evaluate(["fix A", "fix B", "fix C"])
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.proposals, ["fix A", "fix B"])

    def test_rejects_when_validation_fails(self):
        gate = PatchGate(lambda: False)
        decision = gate.evaluate(["fix A"])
        self.assertFalse(decision.accepted)
        self.assertIn("Validation failed", decision.reason)

    def test_never_accepts_empty_proposals(self):
        gate = PatchGate(lambda: True)
        decision = gate.evaluate([])
        self.assertFalse(decision.accepted)


if __name__ == "__main__":
    unittest.main()
