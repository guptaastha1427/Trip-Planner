"""Support FAQ routing evaluation."""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import patch

from eval.helpers.io import load_jsonl
from services.rag.support_faq import answer_support_query


def _classify_route(
    message: str,
    reply: str,
    *,
    rag_calls: int,
    rag_loose: bool,
) -> str:
    text = (message or "").strip().lower()
    if not text:
        return "empty"
    if text in ("hi", "hello", "hey", "help"):
        return "greeting"
    if any(k in text for k in ("blacklist", "restricted", "ban", "appeal", "account status")):
        return "account_status"
    if "refund" in text and "status" in text:
        return "refund_status"
    upper = (message or "").upper().split()
    if "booking" in text or any(tok.startswith("BK-") for tok in upper):
        if "not found" in (reply or "").lower():
            return "booking_not_found"
        if any(tok.startswith("BK-") for tok in upper):
            return "booking_lookup"
    if rag_calls > 0:
        return "terms_rag_loose" if rag_loose else "terms_rag"
    if "could not find" in (reply or "").lower():
        return "no_match_or_loose"
    return "unknown"


def evaluate_support_row(case: Dict[str, Any]) -> Dict[str, Any]:
    user_id = case["user_id"]
    message = case["message"]
    expected = case["expected_route"]
    expect_escalate = bool(case.get("expect_escalate"))

    call_count = {"n": 0, "loose": False}

    def _count_rag(query, **kwargs):
        call_count["n"] += 1
        if kwargs.get("min_score", 0.42) < 0.4:
            call_count["loose"] = True
        from eval.runners.terms_retrieval import fake_terms_store
        from services.rag.terms_rag import answer_from_terms_document as real

        with patch("services.rag.website_rag.get_terms_vector_store", return_value=fake_terms_store()), patch(
            "services.rag.website_rag.MIN_RELEVANCE_SCORE", 0.0
        ):
            return real(query, **kwargs)

    with patch("services.rag.support_faq.answer_from_terms_document", side_effect=_count_rag):
        reply, escalate, _sources = answer_support_query(user_id, message)

    route = _classify_route(
        message,
        reply,
        rag_calls=call_count["n"],
        rag_loose=call_count["loose"],
    )

    route_ok = route == expected
    if expected == "terms_rag" and route in ("terms_rag", "terms_rag_loose"):
        route_ok = True
    if expected == "no_match_or_loose" and route in ("no_match_or_loose", "terms_rag_loose"):
        route_ok = True

    esc_ok = escalate == expect_escalate
    if expected in ("greeting", "empty", "booking_lookup", "refund_status"):
        pass_ok = route_ok
    else:
        pass_ok = route_ok and esc_ok

    return {
        "test_id": case["test_id"],
        "expected_route": expected,
        "actual_route": route,
        "escalate": escalate,
        "expect_escalate": expect_escalate,
        "route_match": route_ok,
        "escalate_match": esc_ok,
        "pass": pass_ok,
        "reply_preview": (reply or "")[:200],
    }


def run_support_faq_eval(dataset_name: str = "support_faq_routing.jsonl") -> Dict[str, Any]:
    cases = load_jsonl(dataset_name)
    rows = [evaluate_support_row(c) for c in cases]
    route_acc = sum(1 for r in rows if r["route_match"]) / max(len(rows), 1)
    passed = sum(1 for r in rows if r.get("pass"))
    return {
        "summary": {
            "total": len(rows),
            "routing_accuracy": round(route_acc, 4),
            "passed": passed,
            "pass_rate": round(passed / max(len(rows), 1), 4),
        },
        "rows": rows,
    }
