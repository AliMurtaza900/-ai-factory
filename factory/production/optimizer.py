"""Conservative feedback-driven policy recommendations for future videos."""
from __future__ import annotations

from typing import Any

from .analytics import FeedbackStore


class ProductionOptimizer:
    """Turn observed outcomes into explicit, auditable production hints.

    This does not silently rewrite prompts or publish experiments. It produces
    recommendations that can be fed into the next job's metadata.
    """

    def __init__(self, store: FeedbackStore | None = None) -> None:
        self.store = store or FeedbackStore()

    def recommend(self) -> dict[str, Any]:
        metrics = self.store.all()
        if not metrics:
            return {"sample_size": 0, "recommendations": [], "confidence": "none"}
        ranked = self.store.rank()
        top = ranked[: max(1, len(ranked) // 3)]
        avg_ctr = sum(x.ctr for x in top if x.ctr is not None) / max(1, len([x for x in top if x.ctr is not None]))
        avg_ret = sum(x.retention for x in top if x.retention is not None) / max(1, len([x for x in top if x.retention is not None]))
        recommendations: list[str] = []
        if avg_ctr:
            recommendations.append(f"Prefer title/thumbnail patterns from top performers; observed top-group CTR={avg_ctr:.3f}")
        if avg_ret:
            recommendations.append(f"Prefer pacing/structure from top performers; observed top-group retention={avg_ret:.3f}")
        return {
            "sample_size": len(metrics),
            "confidence": "low" if len(metrics) < 5 else "medium" if len(metrics) < 20 else "high",
            "recommendations": recommendations,
            "top_video_ids": [x.video_id for x in ranked[:5]],
        }
