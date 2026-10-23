"""
Retrieve answers from Terms & Policies — vector RAG over the in-app knowledge base.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from services.rag_citations import assistant_message_uses_html, embed_sources_in_reply
from services.ui_copy import polish_ui_copy
from services.website_rag import (
    RetrievedChunk,
    chunks_to_source_dicts,
    format_chunks_as_markdown,
    generate_grounded_answer,
    retrieve_from_terms_kb,
)

# Kept for tests / callers that expect a score threshold metaphor.
DEFAULT_MIN_SCORE = 0.42


def retrieve_policy_chunks(
    query: str,
    *,
    top_k: int = 3,
    min_score: float = DEFAULT_MIN_SCORE,
) -> List[Tuple[float, "PolicyChunk"]]:
    """
    Return (similarity_score, chunk) pairs from semantic search.
    ``min_score`` filters weak matches (higher similarity = better).
    """
    hits, _err = retrieve_from_terms_kb(query, top_k=top_k)
    scored: List[Tuple[float, PolicyChunk]] = []
    for ch in hits:
        if ch.score < min_score:
            continue
        scored.append(
            (
                ch.score,
                PolicyChunk(source=ch.source, text=ch.text, kind="terms"),
            )
        )
    return scored


class PolicyChunk:
    """Lightweight chunk view (compatible with older retrieval code)."""

    __slots__ = ("source", "text", "kind")

    def __init__(self, source: str, text: str, kind: str) -> None:
        self.source = source
        self.text = text
        self.kind = kind


def _low_confidence(chunks: Sequence[RetrievedChunk], min_score: float) -> bool:
    if not chunks:
        return True
    return chunks[0].score < (min_score + 0.08)


def answer_from_terms_document(
    query: str,
    *,
    top_k: int = 3,
    min_score: float = DEFAULT_MIN_SCORE,
) -> Optional[Tuple[str, bool, List[Dict[str, Any]]]]:
    """
    Return (markdown_reply, escalate_suggested, source_chunks) from Terms & Policies.
    ``escalate_suggested`` is True when retrieval confidence is low.
    """
    chunks, err = retrieve_from_terms_kb(query, top_k=top_k)
    if err:
        return (
            polish_ui_copy(
                "I can't search the policy document right now. "
                f"{err} You can still read **Terms & Policies** in the sidebar."
            ),
            True,
            [],
        )

    strong = [c for c in chunks if c.score >= min_score]
    if not strong:
        return None

    answer, llm_err = generate_grounded_answer(query, strong)
    if not answer:
        return None

    body = answer
    if llm_err:
        body = f"{answer}\n\n_{llm_err}_"

    footer = (
        "\n\n_Source: in-app **Terms & Policies** page. "
        "Illustrative text, not a real operator contract._"
    )
    if "Terms & Policies" not in body and "terms" not in body.lower():
        body = f"From the **Terms & Conditions & Policies** document (demo):\n\n{body}"
    if "_Source:" not in body:
        body = body + footer

    sources = chunks_to_source_dicts(strong)
    reply = polish_ui_copy(body)
    if sources and not assistant_message_uses_html(reply):
        reply = embed_sources_in_reply(reply, sources)
    return reply, _low_confidence(strong, min_score), sources


def answer_from_retrieved_chunks(
    query: str,
    chunks: Sequence[RetrievedChunk],
    *,
    min_score: float = DEFAULT_MIN_SCORE,
) -> Optional[Tuple[str, bool, List[Dict[str, Any]]]]:
    """Same as ``answer_from_terms_document`` but with pre-retrieved chunks."""
    strong = [c for c in chunks if c.score >= min_score]
    if not strong:
        return None
    answer, llm_err = generate_grounded_answer(query, strong)
    if not answer:
        answer = format_chunks_as_markdown(strong)
    if llm_err:
        answer = f"{answer}\n\n_{llm_err}_"
    sources = chunks_to_source_dicts(strong)
    reply = polish_ui_copy(answer)
    if sources and not assistant_message_uses_html(reply):
        reply = embed_sources_in_reply(reply, sources)
    return reply, _low_confidence(strong, min_score), sources
