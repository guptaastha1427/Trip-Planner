"""Hybrid semantic + lexical reranking for Terms KB FAISS retrieval."""

from __future__ import annotations

import re
from typing import List, Sequence, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.I)
HYBRID_SEMANTIC_WEIGHT = 0.72
HYBRID_LEXICAL_WEIGHT = 0.28


def _distance_to_similarity(distance: float) -> float:
    return float(1.0 / (1.0 + max(distance, 0.0)))


def keyword_overlap_score(query: str, text: str) -> float:
    tokens = list({m.group(0).lower() for m in _TOKEN_RE.finditer(query or "")})
    if not tokens:
        return 0.0
    blob = (text or "").lower()
    hits = sum(1 for tok in tokens if tok in blob)
    return hits / len(tokens)


def _pairs_to_chunks(pairs: Sequence[Tuple[Document, float]]) -> List:
    from services.rag.website_rag import RetrievedChunk

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


def hybrid_rerank(
    query: str,
    chunks: Sequence,
    *,
    top_k: int,
) -> List:
    from services.rag.website_rag import RetrievedChunk
    """Blend FAISS similarity with token overlap (source + body)."""
    scored: List[Tuple[float, RetrievedChunk]] = []
    for ch in chunks:
        lex = keyword_overlap_score(
            query, f"{ch.source} {ch.text}"
        )
        combined = HYBRID_SEMANTIC_WEIGHT * ch.score + HYBRID_LEXICAL_WEIGHT * lex
        scored.append((combined, ch))

    scored.sort(key=lambda x: x[0], reverse=True)
    out: List[RetrievedChunk] = []
    for combined, ch in scored[:top_k]:
        out.append(
            RetrievedChunk(
                source=ch.source,
                text=ch.text,
                score=round(combined, 4),
                metadata=ch.metadata,
            )
        )
    return out


def fetch_ranked_chunks(
    query: str,
    vector_store: FAISS,
    *,
    top_k: int = 4,
    candidate_k: int | None = None,
    use_hybrid: bool = True,
) -> List:
    """
    Pull a wider FAISS candidate set, optionally hybrid-rerank, return top_k chunks.
    Scores on returned chunks reflect the ranking signal (hybrid or pure semantic).
    """
    q = (query or "").strip()
    if not q:
        return []
    k_fetch = candidate_k or max(top_k * 3, 12)
    pairs = vector_store.similarity_search_with_score(q, k=k_fetch)
    chunks = _pairs_to_chunks(pairs)
    if not chunks:
        return []
    if use_hybrid:
        return hybrid_rerank(q, chunks, top_k=top_k)
    chunks.sort(key=lambda c: c.score, reverse=True)
    return list(chunks[:top_k])
