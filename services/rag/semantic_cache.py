"""
Semantic cache for Terms KB **retrieval chunks only** (not LLM answers).

On hit: reuse stored ``RetrievedChunk`` list; ``generate_grounded_answer`` always runs fresh.
"""

from __future__ import annotations

import json
import math
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from config import (
    DATA_DIR,
    EMBEDDING_CACHE_VERSION,
    get_gemini_embedding_model_candidates,
    get_semantic_cache_max_entries,
    get_semantic_cache_threshold,
)
from services.rag.website_rag import RetrievedChunk, embed_query_text, normalize_query

_CACHE_PATH = DATA_DIR / "rag_retrieval_cache.jsonl"
_lock = threading.Lock()
_store: OrderedDict[str, "CacheEntry"] = OrderedDict()
_loaded = False


@dataclass
class CacheEntry:
    query_normalized: str
    query_embedding: List[float]
    chunks: List[RetrievedChunk]
    top_k: int
    kb_version: str
    embedding_model: str
    created_at: float

    def to_json(self) -> str:
        payload = {
            "query_normalized": self.query_normalized,
            "query_embedding": self.query_embedding,
            "chunks": [
                {
                    "source": c.source,
                    "text": c.text,
                    "score": c.score,
                    "metadata": dict(c.metadata) if c.metadata else {},
                }
                for c in self.chunks
            ],
            "top_k": self.top_k,
            "kb_version": self.kb_version,
            "embedding_model": self.embedding_model,
            "created_at": self.created_at,
        }
        return json.dumps(payload, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        chunks = [
            RetrievedChunk(
                source=str(row.get("source") or "Document"),
                text=str(row.get("text") or ""),
                score=float(row.get("score") or 0),
                metadata=MappingProxyType(dict(row.get("metadata") or {})),
            )
            for row in data.get("chunks") or []
        ]
        return cls(
            query_normalized=str(data.get("query_normalized") or ""),
            query_embedding=[float(x) for x in (data.get("query_embedding") or [])],
            chunks=chunks,
            top_k=int(data.get("top_k") or 0),
            kb_version=str(data.get("kb_version") or ""),
            embedding_model=str(data.get("embedding_model") or ""),
            created_at=float(data.get("created_at") or 0),
        )


def _cache_fingerprint() -> Tuple[str, str]:
    kb = str(EMBEDDING_CACHE_VERSION)
    model = get_gemini_embedding_model_candidates()[0]
    try:
        from services.rag.website_rag import get_embeddings

        emb = get_embeddings()
        if emb is not None:
            model = str(getattr(emb, "model", None) or model)
    except Exception:  # noqa: BLE001
        pass
    return kb, model


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


def _entry_key(entry: CacheEntry) -> str:
    return f"{entry.kb_version}|{entry.embedding_model}|{entry.top_k}|{entry.query_normalized}"


def _load_from_disk() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    if not _CACHE_PATH.is_file():
        return
    kb, model = _cache_fingerprint()
    try:
        lines = _CACHE_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = CacheEntry.from_dict(json.loads(line))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if entry.kb_version != kb or entry.embedding_model != model:
            continue
        _store[_entry_key(entry)] = entry


def _persist_entry(entry: CacheEntry) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CACHE_PATH.open("a", encoding="utf-8") as fh:
            fh.write(entry.to_json() + "\n")
    except OSError:
        pass


def _evict_lru(max_entries: int) -> None:
    while len(_store) > max_entries:
        _store.popitem(last=False)


def lookup(
    query: str,
    *,
    top_k: int,
) -> Tuple[Optional[List[RetrievedChunk]], Dict[str, Any]]:
    """
    Return (chunks, meta) on hit; meta always includes hit flag and similarity when applicable.
    """
    meta: Dict[str, Any] = {
        "hit": False,
        "similarity": None,
        "matched_query_preview": None,
    }
    q_norm = normalize_query(query)
    if not q_norm:
        return None, meta

    kb, model = _cache_fingerprint()
    q_vec = embed_query_text(q_norm)
    if not q_vec:
        return None, meta

    threshold = get_semantic_cache_threshold()
    with _lock:
        _load_from_disk()
        best: Optional[CacheEntry] = None
        best_sim = 0.0
        for entry in _store.values():
            if entry.top_k != top_k:
                continue
            if entry.kb_version != kb or entry.embedding_model != model:
                continue
            sim = _cosine_similarity(q_vec, entry.query_embedding)
            if sim >= threshold and sim > best_sim:
                best_sim = sim
                best = entry
        if best is None:
            return None, meta
        _store.move_to_end(_entry_key(best))
        meta["hit"] = True
        meta["similarity"] = round(best_sim, 4)
        preview = best.query_normalized
        meta["matched_query_preview"] = preview[:80] + ("…" if len(preview) > 80 else "")
        return list(best.chunks), meta


def store(query: str, *, top_k: int, chunks: Sequence[RetrievedChunk]) -> None:
    if not chunks:
        return
    q_norm = normalize_query(query)
    if not q_norm:
        return
    q_vec = embed_query_text(q_norm)
    if not q_vec:
        return
    kb, model = _cache_fingerprint()
    entry = CacheEntry(
        query_normalized=q_norm,
        query_embedding=q_vec,
        chunks=list(chunks),
        top_k=top_k,
        kb_version=kb,
        embedding_model=model,
        created_at=time.time(),
    )
    key = _entry_key(entry)
    with _lock:
        _load_from_disk()
        _store[key] = entry
        _store.move_to_end(key)
        _evict_lru(get_semantic_cache_max_entries())
    _persist_entry(entry)


def clear_policy_rag_trace() -> None:
    try:
        import streamlit as st

        st.session_state["policy_rag_trace"] = []
    except Exception:  # noqa: BLE001
        pass


def policy_rag_trace_step(step: str, **fields: Any) -> None:
    """Append a policy-RAG-only debug step (retrieval cache + prompt cache metadata)."""
    row: Dict[str, Any] = {"step": step}
    row.update(fields)
    try:
        import streamlit as st

        buf = list(st.session_state.get("policy_rag_trace") or [])
        buf.append(row)
        st.session_state["policy_rag_trace"] = buf[-16:]
    except Exception:  # noqa: BLE001
        pass


def record_meta_to_session(meta: Dict[str, Any]) -> None:
    try:
        import streamlit as st

        enriched = dict(meta)
        enriched["step"] = (
            "semantic_cache_hit" if meta.get("hit") else "semantic_cache_miss"
        )
        st.session_state["last_semantic_cache_meta"] = enriched
        policy_rag_trace_step(
            enriched["step"],
            similarity=enriched.get("similarity"),
            matched_query_preview=enriched.get("matched_query_preview"),
        )
    except Exception:  # noqa: BLE001 — optional outside Streamlit
        pass
