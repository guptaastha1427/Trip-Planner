"""
FAQ content and support bot — user-specific lookups + Terms & Policies RAG.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from services.bookings import get_booking, list_bookings_for_user
from services.customer_portal_store import (
    effective_account_profile,
    list_refunds_for_user,
)
from services.demo_users import account_status_label
from services.refund_policy_config import POLICIES, get_policy
from services.terms_content import FAQ_ITEMS
from services.terms_rag import answer_from_terms_document
from services.ui_copy import polish_ui_copy

TICKET_CATEGORIES = [
    "Refund Issue",
    "Booking Issue",
    "Cancellation",
    "Account Restriction",
    "Technical Problem",
    "Other",
]


def _append_terms_context(base: str, query: str) -> str:
    """Add a short policy excerpt when we answer with live user data."""
    rag = answer_from_terms_document(query, top_k=1, min_score=0.42)
    if not rag:
        return base
    reply, _, _sources = rag
    # Only append if not duplicate wall of text
    if len(reply) > 800:
        return f"{base}\n\n---\n\n{reply}"
    return f"{base}\n\n{reply}"


def _reply(
    text: str,
    escalate: bool,
    sources: List[Dict[str, Any]] | None = None,
) -> Tuple[str, bool, List[Dict[str, Any]]]:
    return polish_ui_copy(text), escalate, sources or []


def answer_support_query(
    user_id: str,
    message: str,
) -> Tuple[str, bool, List[Dict[str, Any]]]:
    """
    Return (reply, escalate_suggested, retrieved_sources).
    Policy answers are retrieved from Terms & Policies (vector RAG).
    """
    text = (message or "").strip().lower()
    if not text:
        return _reply(
            "Please ask about bookings, refunds, packages, or account rules. "
            "I answer from the **Terms & Policies** document.",
            False,
        )

    if text in ("hi", "hello", "hey", "help"):
        return _reply(
            "Hello! I answer using the **Terms & Conditions & Policies** text plus your "
            "account data. Try: package cancellation rules, refund eligibility, "
            "support tickets, or your refund status.",
            False,
        )

    # Live account status — then cite terms on restrictions
    if any(k in text for k in ("blacklist", "restricted", "ban", "appeal", "account status")):
        prof = effective_account_profile(user_id)
        status = account_status_label(prof.get("account_status", "active"))
        live = (
            f"Your account status is **{status}**. "
            "See **Account Status** for restriction details."
        )
        rag = answer_from_terms_document(message, top_k=2, min_score=0.38)
        if rag:
            reply, escalate, sources = rag
            return _reply(
                f"{live}\n\n{reply}",
                escalate or prof.get("account_status") not in ("active",),
                sources,
            )
        return _reply(
            live + " You can submit an appeal or open a ticket under Account Restriction.",
            prof.get("account_status") not in ("active",),
        )

    # Live refund queue for this user
    if "refund" in text and "status" in text:
        refunds = list_refunds_for_user(user_id)
        if not refunds:
            rag = answer_from_terms_document("refund processing procedure workflow", top_k=1)
            if rag:
                extra, _esc, sources = rag
            else:
                extra, sources = "Start from **My Bookings & Refunds**.", []
            return _reply(f"You have no refund requests yet. {extra}", False, sources)
        latest = refunds[-1]
        live = (
            f"Latest request **{latest.get('request_id')}** for booking "
            f"**{latest.get('booking_id')}**: workflow **{latest.get('workflow_status')}** "
            f"({latest.get('eligibility')})."
        )
        return _reply(
            _append_terms_context(live, "refund processing procedure"),
            latest.get("workflow_status") == "Rejected",
        )

    # Live booking lookup
    if "booking" in text or any(tok.startswith("BK-") for tok in message.upper().split()):
        tokens = message.upper().split()
        for tok in tokens:
            if tok.startswith("BK-"):
                b = get_booking(tok)
                if not b or b.get("user_id") != user_id:
                    return _reply("That booking was not found for your account.", False)
                pol = get_policy(str(b.get("policy_id", "")))
                pol_name = pol.label if pol else "Unknown policy"
                live = (
                    f"**{tok}**: {b.get('origin')} → {b.get('destination')}, "
                    f"status **{b.get('status')}**, policy **{pol_name}**."
                )
                q = pol.description if pol else "cancellation refund policy"
                return _reply(_append_terms_context(live, q), False)

    # Primary path: Terms & Policies RAG
    rag = answer_from_terms_document(message, top_k=3, min_score=0.42)
    if rag:
        reply, low_conf, sources = rag
        return _reply(reply, low_conf, sources)

    # Slightly looser retrieval before escalating
    rag_loose = answer_from_terms_document(message, top_k=3, min_score=0.32)
    if rag_loose:
        reply, _, sources = rag_loose
        return _reply(reply, True, sources)

    return _reply(
        "I could not find a clear match in **Terms & Policies**. "
        "Please rephrase, open **Terms & Policies** in the sidebar, or create a support ticket.",
        True,
    )


def policy_summary_markdown() -> str:
    lines = [
        "| Mode | Ticket | Refundability | Min hours before departure |",
        "|------|--------|---------------|----------------------------|",
    ]
    for p in POLICIES.values():
        lines.append(
            f"| {p.travel_mode} | {p.ticket_type} | {p.refundability} | {p.min_hours_before_departure} |"
        )
    return "\n".join(lines)
