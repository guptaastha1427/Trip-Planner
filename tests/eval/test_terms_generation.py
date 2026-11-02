"""Terms RAG generation code checks (LLM off)."""

from eval.runners.terms_retrieval import run_terms_generation_eval


def test_terms_generation_smoke():
    out = run_terms_generation_eval()
    assert out["summary"]["total"] >= 28
    assert out["summary"]["mode"] == "markdown_fallback_no_gemini"
