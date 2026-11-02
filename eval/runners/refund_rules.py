"""Refund rules engine evaluation (non-RAG)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from eval.helpers.io import load_jsonl
from services.portal.bookings import get_booking
from services.portal.refund_eligibility import evaluate_refund_request


def _parse_now(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", ""))


def evaluate_refund_row(case: Dict[str, Any]) -> Dict[str, Any]:
    booking_id = case["booking_id"]
    booking = get_booking(booking_id)
    if booking is None:
        return {
            "test_id": case["test_id"],
            "pass": case.get("expect_error") == "missing_booking",
            "error": "missing_booking",
        }

    ev = evaluate_refund_request(
        booking,
        case["user_id"],
        case.get("account_status", "active"),
        None,
        case.get("reason", "change_plans"),
        now=_parse_now(case["now"]),
    )

    ok = ev.eligibility == case.get("expected_eligibility")
    if "min_estimated_refund" in case:
        ok = ok and ev.estimated_refund >= case["min_estimated_refund"]
    if "max_estimated_refund" in case:
        ok = ok and ev.estimated_refund <= case["max_estimated_refund"]

    return {
        "test_id": case["test_id"],
        "booking_id": booking_id,
        "expected_eligibility": case.get("expected_eligibility"),
        "actual_eligibility": ev.eligibility,
        "estimated_refund": ev.estimated_refund,
        "pass": ok,
    }


def run_refund_rules_eval(dataset_name: str = "refund_decision_table.jsonl") -> Dict[str, Any]:
    cases = load_jsonl(dataset_name)
    rows = [evaluate_refund_row(c) for c in cases]
    passed = sum(1 for r in rows if r.get("pass"))
    return {
        "summary": {
            "total": len(rows),
            "passed": passed,
            "pass_rate": round(passed / max(len(rows), 1), 4),
        },
        "rows": rows,
    }
