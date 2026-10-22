"""Shared Streamlit layout for customer portal pages."""

from __future__ import annotations

import html
from typing import Optional

import streamlit as st

from services.customer_portal_store import (
    effective_account_profile,
    get_portal_state,
    persist_portal_state,
    set_demo_user,
)
from services.demo_dashboard import is_admin_dashboard_mode
from services.demo_users import DEMO_USERS, account_status_label
from services.portal_session_ui import clear_ephemeral_portal_ui
from services.ui_copy import polish_ui_copy
from services.role_dashboard import (
    PAGE_BOOKINGS,
    PAGE_REFUND_BOT,
    PAGE_ACCOUNT,
    PAGE_SUPPORT,
    PAGE_TERMS,
    render_page_context_strip,
)
from services.rag_chat_auth import current_user, is_logged_in, logout_user
from services.ui_animations import inject_ui_animations


def inject_portal_styles() -> None:
    inject_ui_animations()
    st.markdown(
        """
        <style>
        .portal-hero {
            background: linear-gradient(135deg, #0f172a 0%, #115e59 55%, #0d9488 120%);
            color: #f8fafc;
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin: 0 0 0.85rem 0;
            transition: all 0.3s ease-in-out;
        }
        .portal-hero h1 {
            font-size: 1.65rem !important;
            color: #f8fafc !important;
            margin: 0 0 0.35rem 0 !important;
        }
        .portal-hero p {
            margin: 0;
            opacity: 0.92;
            font-size: 0.95rem;
        }
        .status-pill {
            display: inline-block;
            padding: 0.2rem 0.65rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .status-pill--ok { background: #d1fae5; color: #065f46; }
        .status-pill--warn { background: #fef3c7; color: #92400e; }
        .status-pill--bad { background: #fee2e2; color: #991b1b; }
        .status-pill--info { background: #e0f2fe; color: #075985; }
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] {
            position: sticky !important;
            bottom: 0 !important;
            z-index: 30 !important;
            background: rgba(255, 255, 255, 0.96) !important;
            border-top: 1px solid rgba(199, 210, 254, 0.65) !important;
            padding: 0.35rem 0 0.5rem !important;
            margin-top: 0.5rem !important;
            box-shadow: 0 -10px 28px rgba(74, 71, 138, 0.08);
            backdrop-filter: blur(12px);
        }
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] button {
            border-radius: 12px !important;
            min-height: 2.75rem !important;
            font-weight: 600 !important;
            text-align: left !important;
            justify-content: flex-start !important;
        }
        .portal-user-dock-wrap {
            position: relative;
            margin-bottom: 0.15rem;
        }
        .portal-user-switch-hint {
            position: absolute;
            left: 0;
            right: 0;
            bottom: calc(100% + 4px);
            background: #ffffff;
            border: 1px solid rgba(199, 210, 254, 0.7);
            border-radius: 12px;
            padding: 0.45rem 0.55rem;
            box-shadow: 0 12px 32px rgba(74, 71, 138, 0.12);
            opacity: 0;
            pointer-events: none;
            transform: translateY(6px);
            transition: opacity 0.18s ease, transform 0.18s ease;
            font-size: 0.78rem;
            color: #475569;
            z-index: 40;
        }
        .portal-user-dock-wrap:hover .portal-user-switch-hint {
            opacity: 1;
            transform: translateY(0);
        }
        .portal-user-switch-row {
            padding: 0.2rem 0;
            border-bottom: 1px solid #f1f5f9;
        }
        .portal-user-switch-row:last-child {
            border-bottom: none;
        }
        .portal-user-switch-cta {
            display: block;
            margin-top: 0.35rem;
            font-size: 0.7rem;
            color: #0d9488;
            font-weight: 600;
        }
        .portal-user-avatar-dot {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 50%;
            background: linear-gradient(135deg, #0d9488, #2563eb);
            color: #fff;
            font-size: 0.72rem;
            font-weight: 700;
            margin-right: 0.35rem;
            vertical-align: middle;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


_HERO_GRADIENTS = {
    PAGE_BOOKINGS: "linear-gradient(135deg, #1e3a5f 0%, #0d9488 60%, #14b8a6 120%)",
    PAGE_REFUND_BOT: "linear-gradient(135deg, #312e81 0%, #6366f1 55%, #818cf8 120%)",
    PAGE_ACCOUNT: "linear-gradient(135deg, #7f1d1d 0%, #b45309 50%, #f59e0b 120%)",
    PAGE_SUPPORT: "linear-gradient(135deg, #0c4a6e 0%, #0284c7 55%, #38bdf8 120%)",
    PAGE_TERMS: "linear-gradient(135deg, #1e293b 0%, #475569 50%, #64748b 120%)",
}


def render_portal_hero(title: str, subtitle: str, page_kind: str = PAGE_TERMS) -> None:
    gradient = _HERO_GRADIENTS.get(
        page_kind, "linear-gradient(135deg, #0f172a 0%, #115e59 55%, #0d9488 120%)"
    )
    st.markdown(
        f"""
        <div class="portal-hero" style="background: {gradient};">
          <h1>{html.escape(polish_ui_copy(title))}</h1>
          <p>{html.escape(polish_ui_copy(subtitle))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _status_pill_class(status: str) -> str:
    s = (status or "").lower()
    if s in ("active", "approved", "completed (demo)", "eligible", "resolved", "closed"):
        return "status-pill--ok"
    if s in ("under review", "in progress", "submitted", "partially eligible", "manual review required"):
        return "status-pill--warn"
    if s in ("rejected", "not eligible", "blacklisted", "temporarily_restricted"):
        return "status-pill--bad"
    return "status-pill--info"


def status_badge(label: str, status: str) -> None:
    cls = _status_pill_class(status)
    display_status = polish_ui_copy(status)
    display_label = polish_ui_copy(label)
    st.markdown(
        f'<span class="status-pill {cls}">{html.escape(display_label)}: {html.escape(display_status)}</span>',
        unsafe_allow_html=True,
    )


def _on_demo_user_changed() -> None:
    uid = st.session_state.get("portal_demo_user_select")
    if uid:
        set_demo_user(uid)
        clear_ephemeral_portal_ui()


def _sync_demo_user_state() -> str:
    current = st.session_state.get("demo_user_id") or get_portal_state().get(
        "current_user_id", "user_alex"
    )
    options = list(DEMO_USERS.keys())
    if current not in options:
        current = options[0]
    if "portal_demo_user_select" not in st.session_state:
        st.session_state.portal_demo_user_select = current
    if st.session_state.get("demo_user_id") != st.session_state.portal_demo_user_select:
        set_demo_user(st.session_state.portal_demo_user_select)
    choice = st.session_state.portal_demo_user_select
    if st.session_state.get("demo_user_id") != choice:
        set_demo_user(choice)
    return choice


def render_sidebar_user_dock() -> str:
    """Bottom-left sidebar profile — signed-in app user + optional booking demo profile."""
    get_portal_state()
    choice = _sync_demo_user_state()
    options = list(DEMO_USERS.keys())
    labels = {uid: DEMO_USERS[uid]["display_name"] for uid in options}

    auth = current_user()
    if auth:
        auth_name = str(auth.get("username") or "User")
        auth_email = str(auth.get("email") or "")
        auth_tokens = [t for t in auth_name.split() if t and t[0].isalpha()]
        auth_initials = "".join(t[0].upper() for t in auth_tokens[:2]) or "U"
        auth_short = auth_name if len(auth_name) <= 20 else auth_name[:18] + "…"
        pop_label = f"{auth_initials}  {auth_short}"
    else:
        profile = effective_account_profile(choice)
        name = labels.get(choice, choice)
        email = DEMO_USERS.get(choice, {}).get("email", "")
        status = account_status_label(profile.get("account_status", "active"))
        tokens = [t for t in name.replace("(", " ").split() if t and t[0].isalpha()]
        initials = "".join(t[0].upper() for t in tokens[:2]) or "U"
        short = name.split("(")[0].strip()
        if len(short) > 20:
            short = short[:18] + "…"
        pop_label = f"{initials}  {short}"

    others = [
        f'<div class="portal-user-switch-row">{html.escape(labels[u])}</div>'
        for u in options
        if u != choice
    ]
    hint = (
        "".join(others)
        + '<span class="portal-user-switch-cta">Click profile below for account options</span>'
    )

    with st.sidebar.container(key="portal_user_dock"):
        st.markdown(
            f'<div class="portal-user-dock-wrap"><div class="portal-user-switch-hint">{hint}</div></div>',
            unsafe_allow_html=True,
        )
        with st.popover(pop_label, use_container_width=True):
            if auth:
                st.markdown(
                    f'<span class="portal-user-avatar-dot">{html.escape(auth_initials)}</span> '
                    f"**{html.escape(auth_name)}**",
                    unsafe_allow_html=True,
                )
                st.caption(auth_email)
                st.caption("_Signed in — session active across all pages._")
                if st.button("Sign out", key="portal_global_sign_out", use_container_width=True):
                    logout_user()
                    st.session_state["rag_chat_menu"] = "Sign up / Sign in"
                    try:
                        import app as trip_app

                        st.switch_page(trip_app.DOCUMENT_ASSISTANT_PAGE)
                    except Exception:
                        st.rerun()
                st.divider()
                st.caption("**Booking & refund preview** (sample customer data)")
            else:
                profile = effective_account_profile(choice)
                name = labels.get(choice, choice)
                email = DEMO_USERS.get(choice, {}).get("email", "")
                status = account_status_label(profile.get("account_status", "active"))
                tokens = [t for t in name.replace("(", " ").split() if t and t[0].isalpha()]
                initials = "".join(t[0].upper() for t in tokens[:2]) or "U"
                st.markdown(
                    f'<span class="portal-user-avatar-dot">{html.escape(initials)}</span> '
                    f"**{html.escape(name)}**",
                    unsafe_allow_html=True,
                )
                st.caption(f"{email}")
                st.caption(f"Account: **{status}**")
                try:
                    import app as trip_app

                    st.page_link(
                        trip_app.DOCUMENT_ASSISTANT_PAGE,
                        label="Sign in / Create account",
                        icon="🔐",
                    )
                except Exception:
                    pass
                st.caption("_Sign in to unlock Document Assistant chat._")

            if is_admin_dashboard_mode():
                st.caption("_Admin preview — pick a customer account._")
            st.radio(
                "Switch account",
                options=options,
                format_func=lambda x: labels[x],
                key="portal_demo_user_select",
                on_change=_on_demo_user_changed,
                label_visibility="collapsed",
            )
    return choice


def render_demo_user_selector() -> str:
    """Alias — user dock at bottom of sidebar."""
    return render_sidebar_user_dock()


def render_portal_sidebar_nav() -> None:
    st.sidebar.header("Customer portal")
    try:
        import app as trip_app

        st.sidebar.page_link(trip_app.TRIP_PLANNER_PAGE, label="Trip Planner", icon="🏠")
        st.sidebar.page_link(trip_app.BOOKINGS_PAGE, label="My Bookings & Refunds", icon="🧳")
        st.sidebar.page_link(trip_app.REFUND_BOT_PAGE, label="Refund Assistant", icon="🤖")
        st.sidebar.page_link(trip_app.TERMS_PAGE, label="Terms & Policies", icon="📜")
        st.sidebar.page_link(trip_app.ACCOUNT_PAGE, label="Account Status", icon="🛡️")
        st.sidebar.page_link(trip_app.SUPPORT_PAGE, label="Help & Support", icon="💬")
        if is_admin_dashboard_mode():
            st.sidebar.page_link(trip_app.ADMIN_PAGE, label="Admin dashboard", icon="🔧")
        st.sidebar.page_link(trip_app.DEV_DOCS_PAGE, label="Developer docs", icon="📘")
    except Exception:
        pass


def portal_page_setup(
    title: str,
    subtitle: str,
    *,
    page_kind: str = PAGE_TERMS,
    show_page_strip: bool = True,
) -> str:
    inject_portal_styles()
    render_portal_hero(title, subtitle, page_kind=page_kind)
    if is_logged_in():
        auth = current_user() or {}
        st.caption(
            f"App session: **{auth.get('username', 'User')}** · {auth.get('email', '')}"
        )
    if show_page_strip:
        user_id = _sync_demo_user_state()
        render_page_context_strip(page_kind, user_id)
    else:
        user_id = _sync_demo_user_state()
    st.session_state.demo_user_id = user_id
    persist_portal_state()
    return user_id
