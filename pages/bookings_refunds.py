"""My Bookings & Refunds — demo bookings and refund requests."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from services.bookings import enrich_booking_display, list_bookings_for_user
from services.customer_portal_store import (
    add_refund_request,
    effective_account_profile,
    find_refund_for_booking,
    list_refunds_for_user,
    new_id,
)
from services.demo_dashboard import is_admin_dashboard_mode
from services.portal_ui import portal_page_setup, status_badge
from services.role_dashboard import PAGE_BOOKINGS
from services.refund_eligibility import evaluate_refund_request
from services.refund_policy_config import REFUND_REASONS
from services.package_booking_ui import render_book_package_tab
from services.portal_display import (
    booking_detail_markdown,
    booking_for_refund_display,
    format_portal_datetime,
    refund_reason_label,
)
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy


def _format_dt(raw: str) -> str:
    if not raw:
        return "—"
    try:
        return datetime.fromisoformat(raw).strftime("%d %b %Y, %H:%M")
    except ValueError:
        return raw


def render() -> None:
    user_id = portal_page_setup(
        "My Bookings & Refunds",
        "View bookings, submit refund requests, and track refund status.",
        page_kind=PAGE_BOOKINGS,
    )
    profile = effective_account_profile(user_id)

    if is_admin_dashboard_mode():
        st.markdown(
            f"**Customer preview** — bookings and refunds for "
            f"**{profile.get('display_name', user_id)}** only."
        )

    tab_book, tab_bookings, tab_refunds = st.tabs(
        ["Book package", "My bookings", "Refund requests"],
        key="bookings_portal_tabs",
    )

    with tab_book:
        render_book_package_tab(user_id)

    with tab_bookings:
        section_heading("Your bookings", variant="travel")
        bookings = [enrich_booking_display(b) for b in list_bookings_for_user(user_id)]
        if not bookings:
            st.info("No bookings yet — use **Book package** to create one.")
        for b in bookings:
            title = b.get("display_title") or (
                f"{b.get('booking_id')} · {b.get('origin')} → {b.get('destination')}"
            )
            with st.expander(title, expanded=False):
                cols = st.columns(3)
                if b.get("package_name"):
                    st.markdown(f"**Package:** {b.get('package_name')} — _{b.get('package_tagline', '')}_")
                    st.caption(
                        f"Travelers: **{b.get('travelers', 1)}** · "
                        f"Nights: **{b.get('nights', '—')}**"
                    )
                cols[0].markdown(f"**Mode:** {b.get('travel_mode', '').title()}")
                cols[1].markdown(f"**Status:** {b.get('status')}")
                cols[2].markdown(f"**Amount:** ₹{b.get('booked_amount'):,.0f}")
                st.markdown(f"**Journey:** {_format_dt(b.get('journey_datetime', ''))}")
                st.markdown(
                    f"**Cancellation deadline:** "
                    f"{_format_dt(b.get('cancellation_deadline', ''))}"
                )
                pol = b.get("policy") or {}
                st.caption(polish_ui_copy(pol.get("description", "")))
                existing = find_refund_for_booking(user_id, b["booking_id"])
                if existing:
                    st.warning(
                        f"Refund request **{existing.get('request_id')}** already exists "
                        f"({existing.get('workflow_status')})."
                    )
                else:
                    with st.form(key=f"refund_form_{b['booking_id']}"):
                        reason = st.selectbox(
                            "Refund reason",
                            options=[r[0] for r in REFUND_REASONS],
                            format_func=lambda x: dict(REFUND_REASONS)[x],
                        )
                        submitted = st.form_submit_button("Check eligibility & submit")
                        if submitted:
                            if is_admin_dashboard_mode():
                                st.warning(
                                    "Switch to **👤 User** mode to submit refunds as a customer. "
                                    "In admin mode, manage requests on the **Admin dashboard**."
                                )
                            else:
                                ev = evaluate_refund_request(
                                    b,
                                    user_id,
                                    profile.get("account_status", "active"),
                                    existing,
                                    reason,
                                )
                                st.session_state["last_eval"] = ev.to_dict()
                                st.session_state["last_eval_booking"] = b["booking_id"]
                                if ev.eligibility in ("Not Eligible",):
                                    st.error(ev.reason)
                                elif ev.eligibility == "Manual Review Required":
                                    st.warning(ev.reason)
                                else:
                                    st.success(ev.reason)
                                st.json(ev.to_dict())
                                if ev.workflow_status not in ("Rejected",):
                                    record = {
                                        "request_id": new_id("RR"),
                                        "user_id": user_id,
                                        "booking_id": b["booking_id"],
                                        "reason": reason,
                                        **ev.to_dict(),
                                        "workflow_status": (
                                            "Submitted"
                                            if ev.workflow_status == "Approved"
                                            else ev.workflow_status
                                        ),
                                        "status_history": [
                                            {
                                                "ts": datetime.utcnow().isoformat() + "Z",
                                                "status": "Submitted",
                                            }
                                        ],
                                        "created_at": datetime.utcnow().isoformat() + "Z",
                                    }
                                    if ev.workflow_status == "Approved":
                                        record["status_history"].append(
                                            {
                                                "ts": datetime.utcnow().isoformat() + "Z",
                                                "status": "Approved",
                                            }
                                        )
                                        record["workflow_status"] = "Approved"
                                    add_refund_request(record)
                                    st.success(
                                        f"Refund request created: **{record['request_id']}** "
                                        "(no payment processed)."
                                    )
                                    st.rerun()

    with tab_refunds:
        section_heading("Refund request tracking", variant="travel")
        refunds = list_refunds_for_user(user_id)
        if not refunds:
            st.caption("No refund requests yet.")
        for r in reversed(refunds):
            booking = booking_for_refund_display(str(r.get("booking_id", "")))
            booking_status = (
                str(booking.get("status", "—")).title() if booking else "Unknown"
            )
            refund_status = str(r.get("workflow_status", "Submitted"))
            eligibility = str(r.get("eligibility", "—"))
            reason_label = refund_reason_label(str(r.get("reason", "")))
            header = (
                f"{r.get('request_id')} · booking {r.get('booking_id')} · "
                f"{refund_status}"
            )
            with st.expander(header, expanded=False):
                with st.expander(
                    f"Refund status — {refund_status}",
                    expanded=False,
                ):
                    status_badge("Refund status", refund_status)

                with st.expander(
                    f"Eligibility — {eligibility}",
                    expanded=False,
                ):
                    status_badge("Eligibility", eligibility)
                    detail = r.get("explanation_detail") or r.get("explanation", "")
                    if detail:
                        st.info(detail)

                with st.expander(
                    f"Booking / ticket — {booking_status}",
                    expanded=False,
                ):
                    status_badge("Booking / ticket", booking_status)
                    if booking:
                        st.markdown(booking_detail_markdown(booking))
                    else:
                        st.warning("Linked booking not found.")

                with st.expander(
                    f"Reason — {reason_label}",
                    expanded=False,
                ):
                    st.markdown(
                        f"**Reason you raised this:** {reason_label}"
                    )

                est_refund = float(r.get("estimated_refund", 0) or 0)
                with st.expander(
                    f"Refund estimate — ₹{est_refund:,.0f}",
                    expanded=False,
                ):
                    st.markdown(
                        f"**Original amount:** ₹{r.get('original_amount', 0):,.0f}"
                    )
                    st.markdown(
                        f"**Cancellation fee:** ₹{r.get('cancellation_fee', 0):,.0f}"
                    )
                    st.markdown(
                        f"**Estimated refund:** ₹{est_refund:,.0f}"
                    )
                    if r.get("processing_time"):
                        st.caption(
                            f"Typical processing: "
                            f"{polish_ui_copy(str(r.get('processing_time', '')))}"
                        )

                hist = r.get("status_history") or []
                if hist:
                    with st.expander(
                        f"Status timeline — {len(hist)} update(s)",
                        expanded=False,
                    ):
                        for step in hist:
                            note = step.get("note")
                            extra = f" — {note}" if note else ""
                            st.caption(
                                f"{format_portal_datetime(str(step.get('ts', '')))}: "
                                f"**{polish_ui_copy(str(step.get('status', '')))}**"
                                f"{polish_ui_copy(extra)}"
                            )


render()
