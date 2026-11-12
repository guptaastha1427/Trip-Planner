"""Phase 5 regression gates vs eval/regression_thresholds.json (real embeddings)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.runners.ragas_pipeline import MetricThresholds, run_terms_rag_pipeline
from eval.runners.refund_rules import run_refund_rules_eval
from eval.runners.support_faq import run_support_faq_eval
from eval.runners.wikivoyage import run_wikivoyage_eval

THRESHOLDS_PATH = Path(__file__).resolve().parents[2] / "eval" / "regression_thresholds.json"

pytestmark = pytest.mark.eval_regression


def _load_thresholds() -> dict:
    return json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def terms_pipeline_summary():
    out = run_terms_rag_pipeline(
        thresholds=MetricThresholds(
            k=3,
            answer_correctness=0.0,
            ndcg_at_k=0.0,
            hit_at_k=0.0,
        )
    )
    return out["summary"]


def test_terms_rag_regression_meets_baseline(terms_pipeline_summary):
    floors = _load_thresholds()["terms_rag_pipeline"]
    s = terms_pipeline_summary
    assert s["mrr_mean"] >= floors["mrr_mean_min"]
    assert s.get("hit_rate_at_3", 0) >= floors["hit_rate_at_3_min"]
    assert s.get("ndcg_at_3_mean", 0) >= floors["ndcg_at_3_mean_min"]
    assert s.get("groundedness_mean", 0) >= floors["groundedness_mean_min"]
    assert s.get("answer_correctness_mean", 0) >= floors["answer_correctness_mean_min"]
    canon = s.get("ragas_canonical_mean") or {}
    canon_floors = floors.get("ragas_canonical_mean") or {}
    for key, min_key in (
        ("faithfulness", "faithfulness_min"),
        ("context_recall", "context_recall_min"),
        ("context_precision", "context_precision_min"),
    ):
        if min_key in canon_floors and canon.get(key) is not None:
            assert canon[key] >= canon_floors[min_key]


def test_auxiliary_suites_regression():
    floors = _load_thresholds()
    support = run_support_faq_eval()["summary"]
    assert support["routing_accuracy"] >= floors["support_faq"]["routing_accuracy_min"]
    wiki = run_wikivoyage_eval()["summary"]
    assert wiki["pass_rate"] >= floors["wikivoyage"]["pass_rate_min"]
    refund = run_refund_rules_eval()["summary"]
    assert refund["pass_rate"] >= floors["refund_rules"]["pass_rate_min"]
