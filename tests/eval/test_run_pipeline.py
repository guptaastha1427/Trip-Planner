"""Smoke tests for eval.run_pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from eval.run_pipeline import build_payload, write_artifact
from eval.runners.ragas_pipeline import MetricThresholds


def test_pipeline_builds_per_case_metrics():
    payload = build_payload(
        thresholds=MetricThresholds(k=3, answer_correctness=0.0),
        dataset="terms_rag_golden.jsonl",
        include_auxiliary=False,
    )
    rows = payload["cases"]["terms_rag"]
    assert len(rows) >= 40
    row = rows[0]
    assert "input" in row and "user_query" in row["input"]
    assert "output" in row and "generated_response" in row["output"]
    assert "retrieval_metrics" in row and "mrr" in row["retrieval_metrics"]
    assert "ragas_metrics" in row
    for key in (
        "answer_correctness",
        "context_utilization",
        "hallucination_rate",
        "groundedness",
        "ragas_canonical",
    ):
        assert key in row["ragas_metrics"]
    assert "faithfulness" in row["ragas_metrics"]["ragas_canonical"]
    assert "failure_analysis" in row
    assert "ndcg_at_3" in row["retrieval_metrics"]
    assert "evaluation_mode" in row["ragas_metrics"]
    assert payload.get("evaluation_mode") == "heuristic_offline"
    assert payload.get("retrieval_profile", {}).get("hybrid_enabled") is True
    assert "artifact_lineage" in payload


def test_pipeline_writes_artifact(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "eval.run_pipeline.ARTIFACTS_DIR",
        tmp_path,
    )
    payload = build_payload(
        thresholds=MetricThresholds(),
        dataset="terms_rag_golden.jsonl",
        include_auxiliary=False,
    )
    path = write_artifact(payload, stamp="test_smoke", prefix="baseline")
    assert path.exists()
    assert path.name == "baseline_test_smoke.json"
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["pipeline"] == "eval.run_pipeline"
    assert loaded["artifact"]["prefix"] == "baseline"
    assert "terms_rag_pipeline" in loaded["summary"]
    assert "ragas_canonical_mean" in loaded["summary"]["terms_rag_pipeline"]
    assert loaded.get("evaluation_mode") == "heuristic_offline"
    assert loaded["artifact"].get("summary_csv") == "baseline_test_smoke.csv"
