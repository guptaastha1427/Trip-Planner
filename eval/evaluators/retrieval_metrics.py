"""Retrieval metric calculations for golden datasets."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence


def hit_at_k( #checks if the expected sources are hit at the given rank.
    expected_sources: Sequence[str],
    retrieved_sources: Sequence[str],
    k: int,
    *,
    matcher=None,
) -> bool:
    if matcher is None:
        from eval.helpers.terms_retrieval import source_matches

        matcher = source_matches
    top = list(retrieved_sources)[:k]
    for src in top:
        if matcher(expected_sources, src):
            return True
    return False


def recall_at_k( #calculates the recall at the given rank.
    expected_sources: Sequence[str],
    retrieved_sources: Sequence[str],
    k: int,
    *,
    matcher=None,
) -> float:
    if not expected_sources:
        return 1.0
    if matcher is None:
        from eval.helpers.terms_retrieval import source_matches

        matcher = source_matches
    top = list(retrieved_sources)[:k]
    hits = sum(1 for exp in expected_sources if any(matcher([exp], s) for s in top))
    return hits / len(expected_sources)


def _dcg(relevances: Sequence[float]) -> float:
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def ndcg_at_k( #calculates the NDCG at the given rank.
    expected_sources: Sequence[str],
    retrieved_sources: Sequence[str],
    k: int,
    *,
    matcher=None,
) -> float:
    """Binary-relevance NDCG@K (one relevant doc counts per matching rank)."""
    if not expected_sources or not retrieved_sources:
        return 0.0
    if matcher is None:
        from eval.helpers.terms_retrieval import source_matches

        matcher = source_matches
    top = list(retrieved_sources)[:k]
    relevances = [1.0 if matcher(expected_sources, src) else 0.0 for src in top]
    dcg = _dcg(relevances)
    ideal_len = min(len(expected_sources), k)
    idcg = _dcg([1.0] * ideal_len)
    if idcg <= 0:
        return 0.0
    return dcg / idcg


def hit_rate_at_k( #calculates the hit rate at the given rank.
    expected_sources: Sequence[str],
    retrieved_sources: Sequence[str],
    k: int,
    *,
    matcher=None,
) -> float:
    """Per-query hit indicator as 0.0 or 1.0 (aggregate mean = hit rate)."""
    if not expected_sources:
        return 1.0
    return 1.0 if hit_at_k(expected_sources, retrieved_sources, k, matcher=matcher) else 0.0


def mean_reciprocal_rank( #calculates the mean reciprocal rank.
    expected_sources: Sequence[str],
    retrieved_sources: Sequence[str],
    *,
    matcher=None,
) -> float:
    if matcher is None:
        from eval.helpers.terms_retrieval import source_matches

        matcher = source_matches
    for rank, src in enumerate(retrieved_sources, start=1):
        if matcher(expected_sources, src):
            return 1.0 / rank
    return 0.0


@dataclass
class RetrievalAggregate: #defines a dataclass for the retrieval aggregate.
    count: int = 0
    hit1: float = 0.0
    hit3: float = 0.0
    recall3: float = 0.0
    mrr: float = 0.0
    avg_top1_score: float = 0.0
    low_confidence_pct: float = 0.0
    escalation_accuracy: float = 0.0
    per_case: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]: #converts the retrieval aggregate to a dictionary.
        return {
            "count": self.count,
            "hit_at_1": round(self.hit1, 4),
            "hit_at_3": round(self.hit3, 4),
            "recall_at_3": round(self.recall3, 4),
            "mrr": round(self.mrr, 4),
            "avg_top1_score": round(self.avg_top1_score, 4),
            "low_confidence_pct": round(self.low_confidence_pct, 4),
            "escalation_accuracy": round(self.escalation_accuracy, 4),
        }


def aggregate_retrieval_rows(rows: List[Dict[str, Any]]) -> RetrievalAggregate: #aggregates the retrieval rows.
    agg = RetrievalAggregate(count=len(rows)) #initializes the retrieval aggregate.
    if not rows:
        return agg
    h1 = h3 = rec3 = mrr = top1 = low = esc = 0.0
    for row in rows:
        h1 += 1.0 if row.get("hit_at_1") else 0.0 #adds 1.0 to the hit1 if the expected sources are hit at the given rank.
        h3 += 1.0 if row.get("hit_at_3") else 0.0 #adds 1.0 to the hit3 if the expected sources are hit at the given rank.
        rec3 += float(row.get("recall_at_3") or 0.0) #adds the recall at the given rank to the rec3.
        mrr += float(row.get("mrr") or 0.0) #adds the mean reciprocal rank to the mrr.
        top1 += float(row.get("top1_score") or 0.0)
        if row.get("low_confidence"): 
            low += 1.0
        if row.get("escalation_match"):
            esc += 1.0
    n = len(rows)
    agg.hit1 = h1 / n
    agg.hit3 = h3 / n
    agg.recall3 = rec3 / n
    agg.mrr = mrr / n
    agg.avg_top1_score = top1 / n
    agg.low_confidence_pct = low / n
    agg.escalation_accuracy = esc / n
    agg.per_case = rows
    return agg
