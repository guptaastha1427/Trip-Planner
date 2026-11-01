"""Semantic retrieval cache — chunks only, never LLM output."""

from unittest.mock import MagicMock, patch

from langchain_community.embeddings import FakeEmbeddings

from services.rag.terms_rag import answer_from_terms_document
from services.rag.website_rag import (
    RetrievedChunk,
    _terms_source_documents,
    build_faiss_index,
    retrieve_from_terms_kb,
    similarity_search,
)


def _fake_terms_store():
    return build_faiss_index(_terms_source_documents(), FakeEmbeddings(size=8))


def test_cache_disabled_uses_faiss_only():
    store = _fake_terms_store()
    with patch("config.is_semantic_cache_enabled", return_value=False), patch(
        "services.rag.website_rag.get_terms_vector_store", return_value=store
    ), patch("services.rag.website_rag.MIN_RELEVANCE_SCORE", 0.0), patch(
        "services.rag.website_rag.similarity_search", wraps=similarity_search
    ) as mock_search:
        retrieve_from_terms_kb("refund policy flight", top_k=3)
        retrieve_from_terms_kb("refund policy flight again", top_k=3)
    assert mock_search.call_count == 2


def test_cache_hit_skips_faiss_still_calls_llm():
    store = _fake_terms_store()
    vec = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    sample_chunks = [
        RetrievedChunk(source="Terms — Refunds", text="Demo refund text.", score=0.9)
    ]

    def fake_lookup(query, *, top_k):
        if "paraphrase" in query.lower():
            return list(sample_chunks), {
                "hit": True,
                "similarity": 0.95,
                "matched_query_preview": "what is refund",
            }
        return None, {"hit": False, "similarity": None, "matched_query_preview": None}

    llm_calls = {"n": 0}

    def fake_generate(q, chunks):
        llm_calls["n"] += 1
        return f"Answer for {q[:20]}", None

    with patch("config.is_semantic_cache_enabled", return_value=True), patch(
        "services.rag.website_rag.get_terms_vector_store", return_value=store
    ), patch("services.rag.website_rag.MIN_RELEVANCE_SCORE", 0.0), patch(
        "services.rag.semantic_cache.lookup", side_effect=fake_lookup
    ), patch(
        "services.rag.semantic_cache.store"
    ), patch(
        "services.rag.website_rag.embed_query_text", return_value=vec
    ), patch(
        "services.rag.website_rag.similarity_search", wraps=similarity_search
    ) as mock_search, patch(
        "services.rag.terms_rag.generate_grounded_answer", side_effect=fake_generate
    ):
        answer_from_terms_document("what is refund policy", top_k=3, min_score=0.0)
        answer_from_terms_document("paraphrase refund policy question", top_k=3, min_score=0.0)

    assert mock_search.call_count == 1
    assert llm_calls["n"] == 2
