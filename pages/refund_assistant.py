"""Refund Assistant — interactive eligibility bot (rules enforced server-side)."""

from __future__ import annotations

import streamlit as st

from services.bookings import enrich_booking_display, list_bookings_for_user
from services.customer_portal_store import effective_account_profile, find_refund_for_booking
from services.portal_session_ui import bot_booking_key, bot_eval_ctx_key, bot_eval_key, bot_messages_key
from services.portal_ui import portal_page_setup, status_badge
from services.role_dashboard import PAGE_REFUND_BOT
from services.refund_eligibility import evaluate_refund_request
from services.refund_policy_config import REFUND_REASONS
from services.ui_components import section_heading


def render() -> None:
    user_id = portal_page_setup(
        "Refund Assistant",
        "Eligibility is computed by the rule engine from your ticket policy — not guessed by the UI.",
        page_kind=PAGE_REFUND_BOT,
    )
    profile = effective_account_profile(user_id)
    bookings = list_bookings_for_user(user_id)
    if not bookings:
        st.info("No bookings available for this user.")
        return

    section_heading("Step 1 — Select booking & reason", variant="plan")
    labels = {
        b["booking_id"]: f"{b['booking_id']} ({b['origin']} → {b['destination']})"
        for b in bookings
    }
    bid = st.selectbox("Booking", options=list(labels.keys()), format_func=lambda x: labels[x])
    booking = enrich_booking_display(next(b for b in bookings if b["booking_id"] == bid))
    reason = st.selectbox(
        "Refund reason",
        options=[r[0] for r in REFUND_REASONS],
        format_func=lambda x: dict(REFUND_REASONS)[x],
        key=f"refund_reason_{user_id}",
    )

    pol = booking.get("policy") or {}
    with st.expander("Ticket policy applied to this booking", expanded=True):
        st.markdown(f"**{booking.get('policy_label') or pol.get('label', 'Policy')}**")
        st.caption(pol.get("description", "No policy description."))
        c1, c2, c3 = st.columns(3)
        c1.caption(f"Refundability: **{pol.get('refundability', '—')}**")
        c2.caption(f"Min hours before departure: **{pol.get('min_hours_before_departure', '—')}**")
        c3.caption(f"Mode: **{booking.get('travel_mode', '—')}** / **{booking.get('ticket_type', '—')}**")

    if st.button("Run policy eligibility check", type="primary"):
        existing = find_refund_for_booking(user_id, bid)
        ev = evaluate_refund_request(
            booking,
            user_id,
            profile.get("account_status", "active"),
            existing,
            reason,
        )
        payload = ev.to_dict()
        payload["policy_label"] = booking.get("policy_label") or pol.get("label", "")
        payload["policy_description"] = pol.get("description", ev.explanation_detail)
        payload["eval_reason"] = reason
        st.session_state[bot_eval_key(user_id)] = payload
        st.session_state[bot_booking_key(user_id)] = bid
        st.session_state[bot_eval_ctx_key(user_id)] = {"booking_id": bid, "reason": reason}

    ctx = st.session_state.get(bot_eval_ctx_key(user_id)) or {}
    ev_d = st.session_state.get(bot_eval_key(user_id))
    ctx_ok = ctx.get("booking_id") == bid and ctx.get("reason") == reason
    if ev_d and st.session_state.get(bot_booking_key(user_id)) == bid and ctx_ok:
        section_heading("Eligibility result (rule engine)", variant="travel")
        status_badge("Outcome", ev_d.get("eligibility", "—"))
        st.info(
            f"**Policy:** {ev_d.get('policy_label', 'Policy')} — "
            f"{ev_d.get('policy_description', ev_d.get('explanation_detail', ''))}"
        )
        st.write(ev_d.get("reason"))
        st.caption(f"Reason selected: **{dict(REFUND_REASONS).get(reason, reason)}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Original", f"₹{ev_d.get('original_amount', 0):,.0f}")
        c2.metric("Cancellation fee", f"₹{ev_d.get('cancellation_fee', 0):,.0f}")
        c3.metric("Est. refund", f"₹{ev_d.get('estimated_refund', 0):,.0f}")
        st.markdown(f"**Processing time:** {ev_d.get('processing_time')}")
        st.markdown("**Next steps**")
        for step in ev_d.get("next_steps", []):
            st.markdown(f"- {step}")
        with st.expander("Procedure (refund workflow)"):
            for i, step in enumerate(ev_d.get("procedure_steps", []), 1):
                st.markdown(f"{i}. {step}")
    elif ev_d and not ctx_ok:
        st.warning(
            "Booking or reason changed — click **Run policy eligibility check** again "
            "so the result matches the current policy inputs."
        )

    section_heading("Chat", variant="refine")
    st.caption("Answers re-run the same rule engine for the selected booking and reason.")
    bmk = bot_messages_key(user_id)
    if bmk not in st.session_state:
        st.session_state[bmk] = [
            {
                "role": "assistant",
                "text": "Select a booking, choose a reason, and run the policy check — or ask about fees and timing.",
            }
        ]
    for msg in st.session_state[bmk]:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])

    prompt = st.chat_input("Ask about this booking or refund rules…")
    if prompt:
        st.session_state[bmk].append({"role": "user", "text": prompt})
        reply = _bot_reply(prompt, booking, user_id, profile, reason)
        st.session_state[bmk].append({"role": "assistant", "text": reply})
        st.rerun()


def _bot_reply(prompt: str, booking: dict, user_id: str, profile: dict, reason: str) -> str:
    low = prompt.lower()
    existing = find_refund_for_booking(user_id, booking["booking_id"])

    def _run_eval() -> str:
        ev = evaluate_refund_request(
            booking,
            user_id,
            profile.get("account_status", "active"),
            existing,
            reason,
        )
        pol = booking.get("policy") or {}
        return (
            f"Per **{booking.get('policy_label') or pol.get('label', 'policy')}**: "
            f"**{ev.eligibility}** — {ev.reason} "
            f"Estimated refund: ₹{ev.estimated_refund:,.0f}. "
            f"({pol.get('description', '')[:120]})"
        )

    if "eligible" in low or "refund" in low or "policy" in low:
        return _run_eval()
    if "fee" in low or "charge" in low:
        pol = booking.get("policy") or {}
        ev = evaluate_refund_request(
            booking,
            user_id,
            profile.get("account_status", "active"),
            existing,
            reason,
        )
        return (
            f"Cancellation fee: ₹{ev.cancellation_fee:,.0f}. "
            f"{pol.get('description', 'See Terms & Policies.')}"
        )
    if "time" in low or "processing" in low:
        ev = evaluate_refund_request(
            booking,
            user_id,
            profile.get("account_status", "active"),
            existing,
            reason,
        )
        return f"Estimated processing: {ev.processing_time}"
    return (
        "I use the same policy rules as the check above. Try: "
        "'Am I eligible for a refund?' or 'What are the cancellation fees?'"
    )


render()
