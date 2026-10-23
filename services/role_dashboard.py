"""Page-specific context strips (user vs admin) — avoid repeating the same dashboard everywhere."""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from services.bookings import list_bookings_for_user
from services.admin_console import (
    refund_request_expander_title,
    refund_workflow_is_terminal,
    render_admin_tickets_embedded,
    render_refund_request_details,
)
from services.customer_portal_store import (
    effective_account_profile,
    get_portal_state,
    list_refunds_for_user,
    list_tickets_for_user,
)
from services.demo_dashboard import is_admin_dashboard_mode
from services.demo_users import DEMO_USERS, account_status_label, get_demo_user
from services.portal_user_context import (
    effective_portal_profile,
    portal_user_display_name,
    resolve_portal_user_id,
)
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
        portal_name = portal_user_display_name(resolve_portal_user_id())
        st.markdown(
            f"**Signed in as:** {name}  \n"
            f"<span style='color:#64748b;font-size:0.9rem'>{email} · "
            f"Bookings & trips: **{portal_name}**</span>",
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
    from services.admin_console import (
        get_admin_queue_counts,
        inject_admin_console_styles,
        render_restricted_users_metric,
    )

    inject_admin_console_styles()
    counts = get_admin_queue_counts()

    title = "### 🔧 Admin overview" if compact else "### 🔧 Admin overview"
    st.markdown(title)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Refunds to process", counts["pending_refunds"])
    c2.metric("Open tickets", counts["open_tickets"])
    c3.metric("Appeals waiting", counts["open_appeals"])
    render_restricted_users_metric(c4)

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
        _render_admin_page_strip(page_kind, user_id)
        return

    profile = effective_portal_profile(user_id)
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
            f"Help center for **{portal_user_display_name(user_id)}** — "
            f"**{len(open_tickets)}** open ticket(s)."
        )
    elif page_kind == PAGE_TERMS:
        st.caption(
            "Complete user notice: Trip Planner, package booking, refunds, accounts, support, and admin mode."
        )
    st.divider()


def _render_admin_page_strip(page_kind: str, preview_user_id: str) -> None:
    preview_name = portal_user_display_name(preview_user_id)
    if page_kind not in (PAGE_TERMS, PAGE_REFUND_BOT):
        st.caption(f"**Customer preview:** {preview_name} (`{preview_user_id}`)")
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
        render_admin_account_panel(preview_user_id=preview_user_id)
        return
    if page_kind == PAGE_SUPPORT:
        render_admin_support_panel(preview_user_id=preview_user_id)
        return
    if page_kind == PAGE_BOOKINGS:
        render_admin_bookings_panel(preview_user_id=preview_user_id)
        st.caption(f"Tabs below show **{preview_name}** only.")


def render_admin_bookings_panel(preview_user_id: Optional[str] = None) -> None:
    state = get_portal_state()
    refunds = state.get("refund_requests") or []
    if preview_user_id:
        refunds = [r for r in refunds if r.get("user_id") == preview_user_id]
        section_heading(
            f"Refund requests — {portal_user_display_name(preview_user_id)}",
            variant="travel",
        )
    else:
        section_heading("All refund requests (admin view)", variant="travel")
    if not refunds:
        st.caption("No refund requests in portal state yet.")
        return
    for r in reversed(refunds[-12:]):
        status = str(r.get("workflow_status", "Submitted"))
        with st.expander(
            refund_request_expander_title(r),
            expanded=not refund_workflow_is_terminal(status),
        ):
            render_refund_request_details(r, show_customer=False)


def render_admin_support_panel(
    limit: int = 10,
    *,
    preview_user_id: Optional[str] = None,
) -> None:
    if not is_admin_dashboard_mode():
        st.caption("Switch to **Admin** in the sidebar to manage tickets.")
        return
    heading = "Support tickets (quick actions)"
    if preview_user_id:
        heading = f"Tickets — {portal_user_display_name(preview_user_id)}"
    render_admin_tickets_embedded(
        limit=limit,
        heading=heading,
        user_id=preview_user_id,
    )


def render_admin_account_panel(preview_user_id: Optional[str] = None) -> None:
    state = get_portal_state()
    appeals = state.get("account_appeals") or []
    if preview_user_id:
        profile = effective_portal_profile(preview_user_id)
        user_appeals = [a for a in appeals if a.get("user_id") == preview_user_id]
        section_heading(
            f"Account — {portal_user_display_name(preview_user_id)}",
            variant="travel",
        )
        st.caption(
            f"Status: **{account_status_label(profile.get('account_status', 'active'))}** · "
            f"**{len(user_appeals)}** appeal(s) for this customer."
        )
        for note in profile.get("restriction_notes") or []:
            st.caption(f"· {note.get('summary', '')}")
        for a in user_appeals:
            st.caption(f"Appeal **{a.get('appeal_id')}** — {a.get('status', '—')}")
        return

    overrides = state.get("account_overrides") or {}
    section_heading("Account oversight (admin view)", variant="travel")
    st.caption(f"**{len(appeals)}** appeal(s) in queue · **{len(overrides)}** status override(s) on disk.")
    for uid, ov in overrides.items():
        name = DEMO_USERS.get(uid, {}).get("display_name", uid)
        st.caption(f"`{uid}` ({name}) → **{ov.get('account_status', '—')}**")
