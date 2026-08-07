"""Demonstrate the proposal -> validation -> accept/reject boundary."""

from factory.improvement.patch_gate import PatchGate


def main() -> None:
    proposals = [
        "Inspect the failing behavior against the AgentSpec",
        "Make the smallest change that addresses the observed failure",
        "Re-run the failed test and the complete regression suite",
    ]

    passed = PatchGate(lambda: True).evaluate(proposals)
    print(f"accepted={passed.accepted} proposals={len(passed.proposals)} reason={passed.reason}")

    rejected = PatchGate(lambda: False).evaluate(proposals)
    print(f"accepted={rejected.accepted} proposals={len(rejected.proposals)} reason={rejected.reason}")


if __name__ == "__main__":
    main()
