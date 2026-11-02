"""Wikivoyage TF-IDF retrieval evaluation."""

from __future__ import annotations

import os
from typing import Any, Dict, List
from unittest.mock import patch

from eval.helpers.io import load_jsonl
from services.rag import wikivoyage_rag


def _sample_html(city: str) -> str:
    name = (city or "City").split(",")[0].strip()
    return f"""
<h2>Understand</h2><p>{name} is a popular travel destination with distinct seasons.</p>
<h2>See</h2><p>Visit museums, landmarks, and attractions across {name}.</p>
<h2>Get around</h2><p>Local transportation includes trains, buses, and metro options.</p>
"""


def _offline_fetch(title: str, _ua: str):
    if "Xyznonexistent" in (title or ""):
        return None
    return _sample_html(title)


def evaluate_wikivoyage_row(
    case: Dict[str, Any],
    *,
    enabled: bool = True,
    user_agent: str = "eval-test/1.0 (eval@example.com)",
) -> Dict[str, Any]:
    wikivoyage_rag._RAG_CACHE.clear()
    dest = case.get("destination", "")
    query = case.get("query", "")

    with patch.object(wikivoyage_rag, "_fetch_wikivoyage_article", side_effect=_offline_fetch):
        enabled_result = wikivoyage_rag.retrieve_guides(
            dest, query, user_agent, enabled=enabled
        )
        disabled_result = wikivoyage_rag.retrieve_guides(
            dest, query, user_agent, enabled=False
        )

    chunks = enabled_result.get("chunks") or []
    scores = [c.get("score", 0) for c in chunks]
    keywords = case.get("expected_keywords") or []
    text_blob = " ".join(c.get("text", "") for c in chunks).lower()
    kw_ok = (
        all(kw.lower() in text_blob or kw.lower() in dest.lower() for kw in keywords)
        if keywords
        else True
    )

    ok = enabled_result.get("ok") is True
    if case.get("expect_ok") is False:
        pass_case = (not ok) or len(chunks) < case.get("min_chunks", 1)
    else:
        pass_case = ok and len(chunks) >= case.get("min_chunks", 1) and kw_ok

    disabled_ok = (
        disabled_result.get("ok") is True
        and len(disabled_result.get("chunks") or []) == 0
    )

    return {
        "test_id": case["test_id"],
        "destination": dest,
        "query": query,
        "enabled_chunk_count": len(chunks),
        "disabled_empty": disabled_ok,
        "top_scores": [round(s, 4) for s in scores[:3]],
        "retrieve_guides_executed": True,
        "pass": pass_case and disabled_ok,
    }


def run_wikivoyage_eval(
    dataset_name: str = "wikivoyage_golden.jsonl",
    *,
    live_network: bool = False,
) -> Dict[str, Any]:
    cases = load_jsonl(dataset_name)
    if live_network and os.environ.get("EVAL_LIVE", "").lower() in ("1", "true", "yes"):
        rows: List[Dict[str, Any]] = []
        for case in cases:
            wikivoyage_rag._RAG_CACHE.clear()
            enabled_result = wikivoyage_rag.retrieve_guides(
                case.get("destination", ""),
                case.get("query", ""),
                "trip-planner-eval/1.0 (eval@example.com)",
                enabled=True,
            )
            rows.append(
                {
                    "test_id": case["test_id"],
                    "live": True,
                    "ok": enabled_result.get("ok"),
                    "chunks": len(enabled_result.get("chunks") or []),
                }
            )
        return {"summary": {"mode": "live_network", "rows": len(rows)}, "rows": rows}

    rows = [evaluate_wikivoyage_row(c) for c in cases]
    passed = sum(1 for r in rows if r.get("pass"))
    return {
        "summary": {
            "mode": "mocked_wikivoyage_html",
            "total": len(rows),
            "passed": passed,
            "pass_rate": round(passed / max(len(rows), 1), 4),
        },
        "rows": rows,
    }
