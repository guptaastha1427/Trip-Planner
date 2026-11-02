"""URL scrape / retrieve_from_url eval."""

from eval.runners.url_rag import run_url_rag_eval


def test_url_rag_cases():
    out = run_url_rag_eval()
    assert out["summary"]["production_chat_uses_url_index"] is False
    assert out["summary"]["pass_rate"] >= 0.5
