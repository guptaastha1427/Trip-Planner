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
from services.demo_users import account_status_label
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
from services.portal_user_context import (
    can_pick_customer_preview,
    effective_portal_profile,
    list_portal_customer_ids,
    portal_customer_label,
    portal_user_display_name,
    portal_user_id_for_auth,
    resolve_portal_user_id,
    sync_portal_user_context,
)
from services.rag_chat_auth import current_user, is_logged_in, logout_user
from services.rag_chat_ui import set_rag_chat_menu
from services.ui_animations import inject_ui_animations


def inject_portal_styles() -> None:
    inject_ui_animations()
    st.markdown(
        """
        <style>
        /* Portal pages — align hero with main column gutters (app-wide via inject_ui_animations) */
        [data-testid="stMainBlockContainer"]:has(.portal-hero-wrap) {
            padding-top: var(--tp-main-gutter, 1.25rem) !important;
            padding-left: var(--tp-main-gutter, 1.25rem) !important;
            padding-right: var(--tp-main-gutter, 1.25rem) !important;
        }
        [data-testid="stMainBlockContainer"]:has(.portal-hero-wrap)
            > div > div > [data-testid="stVerticalBlock"] > div:first-child:has([data-testid="stHeading"]) {
            display: none !important;
        }
        [data-testid="stMainBlockContainer"]:has(.portal-hero-wrap) [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        [data-testid="stMainBlockContainer"]:has(.portal-hero-wrap)
            [data-testid="stElementContainer"]:has(.portal-hero-wrap) {
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-left: 0 !important;
            margin-right: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
        }
        .portal-hero-wrap {
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
            margin: 0 0 0.65rem 0;
            padding: 0;
        }
        .portal-hero {
            background: linear-gradient(135deg, #0f172a 0%, #115e59 55%, #0d9488 120%);
            color: #f8fafc;
            border-radius: 16px;
            padding: 1.15rem 1.25rem;
            margin: 0;
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
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
        /* transform on expanded sidebar only — see inject_page_background for collapse rules */
        section[data-testid="stSidebar"][aria-expanded="true"] {
            position: relative !important;
            transform: translateZ(0) !important;
            overflow: visible !important;
        }
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] {
            position: fixed !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            z-index: 30 !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            background: rgba(255, 255, 255, 0.98) !important;
            border-top: none !important;
            padding: 0.5rem 1rem 0.85rem 1rem !important;
            margin: 0 !important;
            box-shadow: 0 -10px 28px rgba(74, 71, 138, 0.1);
            backdrop-filter: blur(12px);
            pointer-events: auto !important;
        }
        section[data-testid="stSidebar"][aria-expanded="false"] [class*="st-key-portal_user_dock"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverBody"] button {
            font-weight: 600 !important;
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
        <div class="portal-hero-wrap">
          <div class="portal-hero" style="background: {gradient};">
            <h1>{html.escape(polish_ui_copy(title))}</h1>
            <p>{html.escape(polish_ui_copy(subtitle))}</p>
          </div>
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
    return sync_portal_user_context()


def _profile_initials(display_name: str) -> str:
    tokens = [t for t in display_name.replace("(", " ").split() if t and t[0].isalpha()]
    return "".join(t[0].upper() for t in tokens[:2]) or "U"


def _profile_display_name(auth: Optional[dict], portal_uid: str) -> str:
    if auth:
        name = str(auth.get("username") or "User")
        return name if len(name) <= 24 else name[:22] + "…"
    short = portal_customer_label(portal_uid).split("(")[0].strip()
    return short if len(short) <= 24 else short[:22] + "…"


def _profile_subtitle(auth: Optional[dict], portal_uid: str) -> str:
    if auth:
        profile = effective_portal_profile(portal_uid)
        return account_status_label(profile.get("account_status", "active"))
    return "Guest · sign in to chat"


def _css_content_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("\r", "")
    )


def _inject_profile_popover_styles(initials: str, name: str, subtitle: str) -> None:
    ini = _css_content_escape(initials)
    nm = _css_content_escape(name)
    sub = _css_content_escape(subtitle)
    st.markdown(
        f"""
        <style>
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopover"] {{
            width: 100% !important;
        }}
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"] {{
            min-height: 3.25rem !important;
            height: auto !important;
            width: 100% !important;
            padding: 0.5rem 0.75rem 0.5rem 3.4rem !important;
            border-radius: 12px !important;
            background: #f1f5f9 !important;
            border: 1px solid rgba(148, 163, 184, 0.35) !important;
            box-shadow: none !important;
            position: relative !important;
            justify-content: flex-start !important;
            overflow: hidden !important;
        }}
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"]:hover {{
            background: #e8edf4 !important;
            border-color: rgba(100, 116, 139, 0.45) !important;
        }}
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"] p,
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"] [data-testid="stMarkdownContainer"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"]::before {{
            content: "{ini}";
            position: absolute;
            left: 0.55rem;
            top: 50%;
            transform: translateY(-50%);
            width: 2.15rem;
            height: 2.15rem;
            border-radius: 50%;
            background: linear-gradient(145deg, #f59e0b 0%, #ea580c 100%);
            color: #fff;
            font-size: 0.82rem;
            font-weight: 700;
            line-height: 2.15rem;
            text-align: center;
        }}
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"]::after {{
            content: "{nm}\\A{sub}";
            white-space: pre;
            display: block;
            text-align: left;
            font-size: 0.88rem;
            font-weight: 600;
            color: #0f172a;
            line-height: 1.2;
            max-width: calc(100% - 0.25rem);
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"] svg,
        section[data-testid="stSidebar"] [class*="st-key-portal_user_dock"] [data-testid="stPopoverButton"] [data-testid="stIconMaterial"] {{
            display: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_user_dock() -> str:
    """Bottom sidebar profile bar (Gemini-style) — popover with sign-in / sign-out."""
    inject_portal_styles()
    get_portal_state()
    choice = resolve_portal_user_id()
    options = list_portal_customer_ids()
    auth = current_user()
    signed_in_uid = portal_user_id_for_auth() if auth else None

    def _customer_radio_label(uid: str) -> str:
        label = portal_customer_label(uid)
        if signed_in_uid and uid == signed_in_uid:
            return f"{label} · signed in"
        return label

    display_name = _profile_display_name(auth, choice)
    initials = _profile_initials(display_name)
    subtitle = _profile_subtitle(auth, choice)

    with st.sidebar.container(key="portal_user_dock"):
        _inject_profile_popover_styles(initials, display_name, subtitle)
        with st.popover(" ", use_container_width=True):
            if auth:
                st.caption(str(auth.get("email") or ""))
            else:
                st.caption("Sign in to use Document Assistant chat across the app.")

            if not auth:
                if st.button("Sign in", key="portal_global_sign_in", use_container_width=True):
                    try:
                        import app as trip_app

                        st.switch_page(trip_app.SIGN_IN_PAGE)
                    except Exception:
                        st.rerun()

            if auth:
                if st.button("Sign out", key="portal_global_sign_out", use_container_width=True):
                    from services.rag_chat_auth import queue_auth_toast

                    former_uid = resolve_portal_user_id()
                    logout_user()
                    set_demo_user(former_uid)
                    st.session_state.portal_demo_user_select = former_uid
                    set_rag_chat_menu(MENU_CHAT)
                    queue_auth_toast("You have been signed out.", "info")
                    st.rerun()

            st.divider()
            if can_pick_customer_preview():
                st.caption("_Switch customer account (admin preview)._")
            else:
                st.caption("_Switch account to preview portal data._")
            st.radio(
                "Switch account",
                options=options,
                format_func=_customer_radio_label,
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
    user_id = resolve_portal_user_id()
    if show_page_strip:
        render_page_context_strip(page_kind, user_id)
    st.session_state.demo_user_id = user_id
    persist_portal_state()
    return user_id
