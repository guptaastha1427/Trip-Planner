"""Terms RAG retrieval metrics (FakeEmbeddings)."""

from eval.runners.terms_retrieval import run_terms_retrieval_eval


def test_terms_retrieval_baseline_runs():
    out = run_terms_retrieval_eval()
    assert out["summary"]["total_cases"] >= 28
    assert out["summary"]["labeled_cases"] >= 20
    assert 0.0 <= out["summary"]["hit_at_3"] <= 1.0


def test_terms_retrieval_metrics_present():
    out = run_terms_retrieval_eval()
    assert out["summary"]["mrr"] is not None
    assert out["summary"]["hit_at_3"] is not None
    # FakeEmbeddings do not reflect production semantic quality — see EVAL_LIVE mode.
