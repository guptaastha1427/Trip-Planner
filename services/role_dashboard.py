"""Page-specific context strips (user vs admin) — avoid repeating the same dashboard everywhere."""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from services.bookings import list_bookings_for_user
from services.admin_console import render_admin_tickets_embedded
from services.portal_display import booking_for_refund_display, refund_reason_label
from services.customer_portal_store import (
    effective_account_profile,
    get_portal_state,
    list_refunds_for_user,
    list_tickets_for_user,
)
from services.demo_dashboard import is_admin_dashboard_mode
from services.demo_users import DEMO_USERS, account_status_label, get_demo_user
from services.rag_chat_auth import current_user, is_logged_in
from services.ui_components import section_heading

# Page identifiers for portal_page_setup(page_kind=...)
PAGE_BOOKINGS = "bookings"
PAGE_REFUND_BOT = "refund_bot"
PAGE_ACCOUNT = "account"
PAGE_SUPPORT = "support"
PAGE_TERMS = "terms"


def render_signed_in_user_banner(user_id: str) -> None:
    """Show the active app login; fall back to demo portal profile when logged out."""
    if is_logged_in():
        auth = current_user() or {}
        name = auth.get("username") or "User"
        email = auth.get("email", "")
        st.markdown(
            f"**Signed in as:** {name}  \n"
            f"<span style='color:#64748b;font-size:0.9rem'>{email} · App session</span>",
            unsafe_allow_html=True,
        )
        return
    profile = effective_account_profile(user_id)
    base = get_demo_user(user_id)
    name = base.get("display_name") or user_id
    email = base.get("email", "")
    status = account_status_label(profile.get("account_status", "active"))
    st.markdown(
        f"**Preview profile:** {name}  \n"
        f"<span style='color:#64748b;font-size:0.9rem'>{email} · Account: {status} · "
        f"Sign in via Document Assistant for a personal session</span>",
        unsafe_allow_html=True,
    )


def render_admin_home_dashboard(compact: bool = False) -> None:
    """Admin snapshot on Trip Planner (admin mode) — links to full console."""
    from services.admin_console import get_admin_queue_counts, inject_admin_console_styles

    inject_admin_console_styles()
    counts = get_admin_queue_counts()

    title = "### 🔧 Admin overview" if compact else "### 🔧 Admin overview"
    st.markdown(title)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Refunds to process", counts["pending_refunds"])
    c2.metric("Open tickets", counts["open_tickets"])
    c3.metric("Appeals waiting", counts["open_appeals"])
    c4.metric("Restricted users", counts["restricted"])

    try:
        import app as trip_app

        st.page_link(
            trip_app.ADMIN_PAGE,
            label="Open interactive admin console",
            icon="🔧",
        )
        st.caption("Refunds, tickets, accounts, and audit — all in one place.")
    except Exception:
        pass
    st.divider()


def render_page_context_strip(page_kind: str, user_id: str) -> None:
    """One short, page-specific header — not the full customer dashboard."""
    if is_admin_dashboard_mode():
        _render_admin_page_strip(page_kind)
        return

    profile = effective_account_profile(user_id)
    bookings = list_bookings_for_user(user_id)
    refunds = list_refunds_for_user(user_id)
    tickets = list_tickets_for_user(user_id)
    open_tickets = [t for t in tickets if (t.get("status") or "").lower() != "resolved"]

    if page_kind == PAGE_BOOKINGS:
        st.caption(
            f"**{len(bookings)}** booking(s) and **{len(refunds)}** refund request(s) — "
            f"book a **travel package** in the first tab."
        )
    elif page_kind == PAGE_REFUND_BOT:
        st.caption(
            "Step-by-step **eligibility checker** for one booking. "
            "To file a request, use **My Bookings & Refunds**."
        )
    elif page_kind == PAGE_ACCOUNT:
        st.caption(
            "Restrictions and appeals for **this account** — "
            f"current status: **{account_status_label(profile.get('account_status', 'active'))}**."
        )
    elif page_kind == PAGE_SUPPORT:
        st.caption(
            f"Help center for **{get_demo_user(user_id).get('display_name', user_id)}** — "
            f"**{len(open_tickets)}** open ticket(s)."
        )
    elif page_kind == PAGE_TERMS:
        st.caption(
            "Complete user notice: Trip Planner, package booking, refunds, accounts, support, and admin mode."
        )
    st.divider()


def _render_admin_page_strip(page_kind: str) -> None:
    if page_kind == PAGE_TERMS:
        st.info("Admin mode — policy reference for all customers.")
        return
    if page_kind == PAGE_REFUND_BOT:
        st.info(
            "Admin mode — use **Refund Assistant** to preview eligibility for a customer. "
            "Process requests on **Admin dashboard**."
        )
        return
    if page_kind == PAGE_ACCOUNT:
        render_admin_account_panel()
        return
    if page_kind == PAGE_SUPPORT:
        render_admin_support_panel()
        return
    if page_kind == PAGE_BOOKINGS:
        render_admin_bookings_panel()
        st.caption("Customer section below previews the selected account only.")


def render_admin_bookings_panel() -> None:
    state = get_portal_state()
    refunds = state.get("refund_requests") or []
    section_heading("All refund requests (admin view)", variant="travel")
    if not refunds:
        st.caption("No refund requests in portal state yet.")
        return
    for r in reversed(refunds[-12:]):
        with st.container(border=True):
            st.markdown(
                f"**{r.get('request_id')}** · user `{r.get('user_id')}` · "
                f"booking **{r.get('booking_id')}** · **{r.get('workflow_status')}**"
            )
            st.markdown(
                f"**Raised because:** {refund_reason_label(str(r.get('reason', '')))} "
                f"· eligibility **{r.get('eligibility', '—')}**"
            )
            booking = booking_for_refund_display(str(r.get("booking_id", "")))
            if booking:
                st.caption(
                    f"Ticket/booking: {booking.get('status', '—')} · "
                    f"{booking.get('origin')} → {booking.get('destination')}"
                )
            expl = r.get("explanation_detail") or r.get("explanation", "")
            if expl:
                st.caption(expl)


def render_admin_support_panel(limit: int = 10) -> None:
    if not is_admin_dashboard_mode():
        st.caption("Switch to **Admin** in the sidebar to manage tickets.")
        return
    render_admin_tickets_embedded(limit=limit, heading="Support tickets (quick actions)")


def render_admin_account_panel() -> None:
    state = get_portal_state()
    appeals = state.get("account_appeals") or []
    overrides = state.get("account_overrides") or {}
    section_heading("Account oversight (admin view)", variant="travel")
    st.caption(f"**{len(appeals)}** appeal(s) in queue · **{len(overrides)}** status override(s) on disk.")
    for uid, ov in overrides.items():
        name = DEMO_USERS.get(uid, {}).get("display_name", uid)
        st.caption(f"`{uid}` ({name}) → **{ov.get('account_status', '—')}**")
