"""One-variable-at-a-time retrieval threshold experiments (eval harness only)."""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import patch

from eval.runners.terms_retrieval import evaluate_terms_retrieval_row, fake_terms_store
from eval.helpers.io import load_jsonl
from services.rag.website_rag import MIN_RELEVANCE_SCORE


def sweep_min_relevance(
    thresholds: List[float] | None = None,
    dataset_name: str = "terms_rag_golden.jsonl",
) -> Dict[str, Any]:
    thresholds = thresholds or [0.32, 0.38, 0.42, 0.48]
    cases = load_jsonl(dataset_name)
    results: List[Dict[str, Any]] = []
    for thr in thresholds:
        rows = [evaluate_terms_retrieval_row(c, min_score=thr) for c in cases]
        labeled = [r for r in rows if r.get("hit_at_3") is not None]
        hit3 = sum(1 for r in labeled if r.get("hit_at_3")) / max(len(labeled), 1)
        esc = sum(1 for r in rows if r.get("escalation_match")) / max(len(rows), 1)
        results.append(
            {
                "min_relevance_score": thr,
                "hit_at_3": round(hit3, 4),
                "escalation_accuracy": round(esc, 4),
                "baseline_production": thr == MIN_RELEVANCE_SCORE,
            }
        )
    return {"experiment": "min_relevance_sweep", "rows": results}
