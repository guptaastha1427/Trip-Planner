"""
Optional Wikivoyage RAG: fetch guide text, chunk, TF-IDF + cosine similarity.

What: retrieve_guides tool returns top-k text chunks for a destination.
Why: Gives the model local travel context beyond raw POI lists.
How: MediaWiki API → HTML strip → paragraph chunks → sklearn TfidfVectorizer.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from config import RAG_CHUNK_MAX, RAG_CHUNK_MIN, RAG_TOP_K, WIKIVOYAGE_API
from services.http_client import get_json

# Module-level cache for vectorizer + matrix per destination (rebuilt when article changes)
_RAG_CACHE: Dict[str, Tuple[TfidfVectorizer, Any, List[dict]]] = {}


def _strip_html(html: str) -> str:
    """Remove tags and collapse whitespace for plain-text RAG."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _chunk_text(text: str) -> List[str]:
    """
    Split on paragraph boundaries; target 800–1000 chars without breaking mid-sentence when possible.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text] if text else []

    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= RAG_CHUNK_MAX:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= RAG_CHUNK_MAX:
                current = para
            else:
                # Long paragraph: split on sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) + 1 <= RAG_CHUNK_MAX:
                        current = f"{current} {sent}".strip()
                    else:
                        if current and len(current) >= RAG_CHUNK_MIN:
                            chunks.append(current)
                        current = sent
    if current and len(current) >= 50:
        chunks.append(current)
    return chunks


@st.cache_data(ttl=86400)
def _fetch_wikivoyage_article(title: str, user_agent: str) -> Optional[str]:
    """Search Wikivoyage and return extract HTML for the best title match."""
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": title,
        "srlimit": 3,
    }
    try:
        search = get_json(WIKIVOYAGE_API, user_agent, params=search_params)
    except Exception:
        return None

    hits = search.get("query", {}).get("search", [])
    if not hits:
        return None

    page_title = hits[0]["title"]
    content_params = {
        "action": "parse",
        "format": "json",
        "page": page_title,
        "prop": "text",
    }
    try:
        parsed = get_json(WIKIVOYAGE_API, user_agent, params=content_params)
    except Exception:
        return None

    html = parsed.get("parse", {}).get("text", {}).get("*")
    return html


def _build_index(destination: str, user_agent: str) -> Optional[List[dict]]:
    """Create chunk metadata list and store TF-IDF index in _RAG_CACHE."""
    html = _fetch_wikivoyage_article(destination, user_agent)
    if not html:
        return None
    plain = _strip_html(html)
    chunks = _chunk_text(plain)
    if not chunks:
        return None

    meta: List[dict] = []
    for i, ch in enumerate(chunks):
        meta.append(
            {
                "chunk_id": f"{destination.lower()[:40]}_{i}",
                "source": f"Wikivoyage:{destination}",
                "text": ch,
            }
        )

    vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
    matrix = vectorizer.fit_transform([m["text"] for m in meta])
    cache_key = destination.lower().strip()
    _RAG_CACHE[cache_key] = (vectorizer, matrix, meta)
    return meta


def retrieve_guides(
    destination: str,
    query: str,
    user_agent: str,
    top_k: int = RAG_TOP_K,
    enabled: bool = True,
) -> Dict[str, Any]:
    """
    Semantic search over Wikivoyage chunks. Returns chunk_id, source, text, score.
    """
    if not enabled:
        return {"ok": True, "chunks": [], "message": "Wikivoyage RAG disabled."}

    destination = (destination or "").strip()
    query = (query or destination).strip()
    if not destination:
        return {"ok": False, "error": "destination is required", "chunks": []}

    cache_key = destination.lower().strip()
    if cache_key not in _RAG_CACHE:
        meta = _build_index(destination, user_agent)
        if not meta:
            return {
                "ok": False,
                "error": "Could not load Wikivoyage article (403 or no page). Try disabling RAG.",
                "chunks": [],
            }
    else:
        _, _, meta = _RAG_CACHE[cache_key]

    vectorizer, matrix, meta = _RAG_CACHE[cache_key]
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix).flatten()
    ranked_idx = scores.argsort()[::-1][:top_k]

    chunks_out = []
    for idx in ranked_idx:
        if scores[idx] <= 0:
            continue
        item = dict(meta[idx])
        item["score"] = float(scores[idx])
        chunks_out.append(item)

    return {"ok": True, "chunks": chunks_out}
