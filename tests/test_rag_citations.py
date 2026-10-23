"""Inline RAG citation formatting."""

from services.rag_citations import (
    assistant_message_uses_html,
    embed_sources_in_reply,
    format_inline_source_citation,
)


def test_url_citation_is_clickable_with_tooltip():
    html = format_inline_source_citation(
        {
            "source": "Example policy",
            "text": "Cancellation within 24 hours.",
            "score": 0.91,
            "metadata": {"url": "https://example.com/policy"},
        }
    )
    assert 'href="https://example.com/policy"' in html
    assert "rag-inline-cite" in html
    assert 'title="' in html
    assert "Cancellation within 24 hours" in html


def test_non_url_citation_uses_span_tooltip():
    html = format_inline_source_citation(
        {
            "source": "Terms — Refunds",
            "text": "Refunds process in 5–10 days.",
            "score": 0.8,
            "metadata": {"details": '{"tier": "demo"}'},
        }
    )
    assert "<span " in html
    assert "Terms — Refunds" in html
    assert "tier" in html


def test_embed_sources_dedupes_and_marks_html():
    out = embed_sources_in_reply(
        "Packages start at demo rates.",
        [
            {"source": "Terms — Packages", "text": "A", "score": 0.5, "metadata": {}},
            {"source": "Terms — Packages", "text": "B", "score": 0.4, "metadata": {}},
        ],
    )
    assert assistant_message_uses_html(out)
    assert out.count("Terms — Packages") == 1
