"""Inline source citations for grounded RAG replies (markdown + HTML tooltips)."""

from __future__ import annotations

import html
import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence
from services.ui_copy import polish_ui_copy
from services.website_rag import validate_http_url

_URL_KEYS = ("url", "source_url", "link", "href", "page_url")
_MAX_TOOLTIP = 420
_MAX_SNIPPET = 240


def _is_http_url(value: str) -> bool:
    ok, _ = validate_http_url((value or "").strip())
    return ok


def _resolve_source_url(src: Mapping[str, Any]) -> Optional[str]:
    meta = src.get("metadata")
    if isinstance(meta, Mapping):
        for key in _URL_KEYS:
            raw = meta.get(key)
            if raw and _is_http_url(str(raw)):
                return str(raw).strip()
    for key in _URL_KEYS:
        raw = src.get(key)
        if raw and _is_http_url(str(raw)):
            return str(raw).strip()
    label = str(src.get("source") or "").strip()
    if _is_http_url(label):
        return label
    return None


def _tooltip_text(src: Mapping[str, Any]) -> str:
    parts: List[str] = []
    snippet = _normalize_whitespace(str(src.get("text") or ""))
    if snippet:
        parts.append(snippet[:_MAX_SNIPPET])
    score = src.get("score")
    if score is not None:
        parts.append(f"Relevance: {score}")

    meta = src.get("metadata")
    if isinstance(meta, Mapping):
        for key in ("details", "extra", "json", "meta"):
            raw = meta.get(key)
            if raw is None:
                continue
            if isinstance(raw, (dict, list)):
                parts.append(
                    json.dumps(raw, ensure_ascii=False)[:_MAX_TOOLTIP]
                )
            elif isinstance(raw, str) and raw.strip().startswith("{"):
                try:
                    parsed = json.loads(raw)
                    parts.append(
                        json.dumps(parsed, ensure_ascii=False)[:_MAX_TOOLTIP]
                    )
                except json.JSONDecodeError:
                    parts.append(raw.strip()[:_MAX_TOOLTIP])
            else:
                parts.append(str(raw).strip()[:_MAX_TOOLTIP])
            break

    return " · ".join(parts) if parts else "Retrieved policy excerpt"


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def format_inline_source_citation(src: Mapping[str, Any]) -> str:
    """
    One citation as HTML (supports ``title`` tooltips; URLs are clickable).
    """
    label = polish_ui_copy(str(src.get("source") or "Source"))
    tip = html.escape(_tooltip_text(src), quote=True)
    url = _resolve_source_url(src)
    safe_label = html.escape(label, quote=False)
    if url:
        safe_url = html.escape(url, quote=True)
        return (
            f'<a class="rag-inline-cite" href="{safe_url}" title="{tip}" '
            f'target="_blank" rel="noopener noreferrer">{safe_label}</a>'
        )
    return f'<span class="rag-inline-cite" title="{tip}">{safe_label}</span>'


def format_inline_citations_block(sources: Sequence[Mapping[str, Any]]) -> str:
    """Comma-separated inline citations (HTML)."""
    if not sources:
        return ""
    seen: set[str] = set()
    cites: List[str] = []
    for src in sources:
        key = str(src.get("source") or "").strip() or json.dumps(src, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        cites.append(format_inline_source_citation(src))
    if not cites:
        return ""
    return ", ".join(cites)


def embed_sources_in_reply(
    reply: str,
    sources: Sequence[Mapping[str, Any]],
    *,
    append_sentence: bool = True,
) -> str:
    """
    Append compact inline citations to the assistant reply (no expander block).
    """
    block = format_inline_citations_block(sources)
    if not block:
        return reply

    body = (reply or "").rstrip()
    if append_sentence:
        return f"{body} ({block})"
    return f"{body}\n\n{block}"


def assistant_message_uses_html(text: str) -> bool:
    return "rag-inline-cite" in (text or "")
