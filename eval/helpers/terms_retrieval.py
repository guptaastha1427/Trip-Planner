"""Eval-only Terms KB retrieval helpers (does not change production logic)."""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

from langchain_community.vectorstores import FAISS

from config import get_terms_retrieval_candidate_multiplier, is_hybrid_terms_retrieval_enabled
from services.rag.hybrid_retrieval import fetch_ranked_chunks
from services.rag.website_rag import MIN_RELEVANCE_SCORE, RetrievedChunk


def raw_similarity_ranked(
    query: str,
    vector_store: FAISS,
    *,
    top_k: int = 10,
) -> List[RetrievedChunk]:
    """Ranked hits (hybrid when enabled) — no MIN_RELEVANCE filter (for MRR / Hit@K)."""
    q = (query or "").strip()
    if not q:
        return []
    mult = get_terms_retrieval_candidate_multiplier()
    candidate_k = max(top_k, top_k * mult, 12)
    return fetch_ranked_chunks(
        q,
        vector_store,
        top_k=top_k,
        candidate_k=candidate_k,
        use_hybrid=is_hybrid_terms_retrieval_enabled(),
    )


def source_matches(expected: Sequence[str], source: str) -> bool:
    s = (source or "").lower()
    for exp in expected:
        if (exp or "").lower() in s:
            return True
    return False


def chunk_preview(text: str, limit: int = 200) -> str:
    t = (text or "").replace("\n", " ").strip()
    if len(t) <= limit:
        return t
    return t[: limit - 1] + "…"


def passes_min_score(score: float, min_score: float = MIN_RELEVANCE_SCORE) -> bool:
    return score >= min_score
