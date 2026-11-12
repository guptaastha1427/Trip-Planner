"""Hybrid retrieval reranking."""

from services.rag.hybrid_retrieval import hybrid_rerank, keyword_overlap_score
from services.rag.website_rag import RetrievedChunk


def test_keyword_overlap_boosts_matching_source():
    score = keyword_overlap_score(
        "refund processing business days",
        "FAQ — How long do demo refunds take? Processing times 2–14 business days",
    )
    assert score >= 0.4


def test_hybrid_rerank_prefers_lexical_match():
    chunks = [
        RetrievedChunk(source="A", text="unrelated", score=0.85, metadata={}),
        RetrievedChunk(
            source="FAQ — Refund",
            text="refund processing business days demo",
            score=0.55,
            metadata={},
        ),
    ]
    out = hybrid_rerank("refund processing business days", chunks, top_k=1)
    assert out[0].source == "FAQ — Refund"
