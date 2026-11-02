"""Wikivoyage retrieve_guides eval (mocked HTML)."""

from eval.runners.wikivoyage import run_wikivoyage_eval


def test_wikivoyage_mocked():
    out = run_wikivoyage_eval()
    assert out["summary"]["mode"] == "mocked_wikivoyage_html"
    assert out["summary"]["pass_rate"] >= 0.75
