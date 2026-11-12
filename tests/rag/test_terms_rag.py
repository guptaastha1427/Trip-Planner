"""Terms RAG retrieval smoke tests."""

from unittest.mock import patch

from services.rag.terms_rag import answer_from_terms_document, retrieve_policy_chunks
from tests.helpers.embeddings import build_terms_vector_store_with_huggingface


def test_retrieve_package_policy():
    store = build_terms_vector_store_with_huggingface()
    with patch("services.rag.website_rag.get_terms_vector_store", return_value=store), patch(
        "services.rag.website_rag.MIN_RELEVANCE_SCORE", 0.0
    ):
        hits = retrieve_policy_chunks(
            "How do travel package bookings and pricing work?",
            top_k=3,
            min_score=0.0,
        )
    assert hits
    assert all(h[0] >= 0.0 for h in hits)
    assert all(h[1].kind == "terms" for h in hits)


def test_answer_cancellation_from_terms():
    store = build_terms_vector_store_with_huggingface()
    with patch("services.rag.website_rag.get_terms_vector_store", return_value=store), patch(
        "services.rag.website_rag.MIN_RELEVANCE_SCORE", 0.0
    ):
        with patch("services.rag.website_rag.get_gemini_api_key", return_value=None):
            out = answer_from_terms_document(
                "flight saver cancellation hours before departure",
                min_score=0.0,
            )
    assert out is not None
    reply, escalate, sources = out
    assert "Terms" in reply
    assert len(reply.strip()) > 40
    assert isinstance(escalate, bool)
    assert isinstance(sources, list)
    assert "rag-inline-cite" in reply
