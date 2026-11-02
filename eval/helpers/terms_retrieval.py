"""Eval-only Terms KB retrieval helpers (does not change production logic)."""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

from langchain_community.vectorstores import FAISS

from services.rag.website_rag import MIN_RELEVANCE_SCORE, RetrievedChunk, _distance_to_similarity


def raw_similarity_ranked(
    query: str,
    vector_store: FAISS,
    *,
    top_k: int = 10,
) -> List[RetrievedChunk]:
    """All top_k FAISS hits with scores — no MIN_RELEVANCE_SCORE filter (for MRR / Hit@K)."""
    q = (query or "").strip()
    if not q:
        return []
    pairs = vector_store.similarity_search_with_score(q, k=top_k)
    out: List[RetrievedChunk] = []
    for doc, dist in pairs:
        sim = _distance_to_similarity(float(dist))
        meta = dict(doc.metadata or {})
        source = str(meta.get("source") or "Document")
        out.append(
            RetrievedChunk(
                source=source,
                text=doc.page_content.strip(),
                score=sim,
                metadata=meta,
            )
        )
    return out


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
