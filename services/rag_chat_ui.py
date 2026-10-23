"""UI helpers for Document & Policy Assistant (auth, terms, navigation)."""

from __future__ import annotations

import streamlit as st

from services.customer_portal_store import set_demo_user
from services.portal_user_context import resolve_portal_user_id
from services.rag_chat_auth import (
    current_user,
    is_logged_in,
    login_user,
    logout_user,
    queue_auth_toast,
    register_user,
)
from services.rag_chat_layout import inject_document_assistant_styles, render_doc_hero
from services.terms_page_ui import render_comprehensive_terms
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy

MENU_SIGNUP = "Sign up / Sign in"
MENU_ACCOUNT = "Account"
MENU_CHAT = "Chat"
MENU_TERMS = "Terms & Conditions"

MENU_OPTIONS = (MENU_CHAT, MENU_TERMS)
MENU_OPTIONS_SIGNED_IN = (MENU_ACCOUNT, MENU_CHAT, MENU_TERMS)

_PENDING_MENU_KEY = "rag_chat_menu_pending"
RAG_OPEN_SIGNIN_KEY = "rag_open_signin"


def open_rag_signin_view() -> None:
    """Open Document Assistant on the sign-in screen (sidebar profile → Sign in)."""
    st.session_state[RAG_OPEN_SIGNIN_KEY] = True
    set_rag_chat_menu(MENU_CHAT)


def set_rag_chat_menu(menu: str) -> None:
    """Apply on the next run before the section radio is drawn."""
    allowed = set(MENU_OPTIONS) | set(MENU_OPTIONS_SIGNED_IN) | {MENU_SIGNUP}
    if menu in allowed:
        st.session_state[_PENDING_MENU_KEY] = menu


def navigate_rag_menu(menu: str) -> None:
    set_rag_chat_menu(menu)
    st.rerun()


def _apply_pending_rag_chat_menu() -> None:
    pending = st.session_state.pop(_PENDING_MENU_KEY, None)
    allowed = set(MENU_OPTIONS) | set(MENU_OPTIONS_SIGNED_IN) | {MENU_SIGNUP}
    if pending in allowed:
        st.session_state["rag_chat_menu"] = pending


def _sync_menu_options_for_auth() -> None:
    """Map auth tab label to signed-in vs signed-out menu sets (before radio renders)."""
    _apply_pending_rag_chat_menu()
    current = st.session_state.get("rag_chat_menu")
    if is_logged_in():
        if current == MENU_SIGNUP:
            set_rag_chat_menu(MENU_ACCOUNT)
            _apply_pending_rag_chat_menu()
    elif current == MENU_ACCOUNT:
        set_rag_chat_menu(MENU_CHAT)
        _apply_pending_rag_chat_menu()


def ensure_document_assistant_menu() -> None:
    """
    Keep the section radio aligned with auth (Streamlit keeps stale values when options change).
    Logged-in users default to Chat instead of the sign-up screen.
    """
    _sync_menu_options_for_auth()
    allowed = MENU_OPTIONS_SIGNED_IN if is_logged_in() else MENU_OPTIONS
    current = st.session_state.get("rag_chat_menu")
    if current not in allowed and current != MENU_SIGNUP:
        st.session_state["rag_chat_menu"] = MENU_CHAT
    elif is_logged_in() and current == MENU_SIGNUP:
        st.session_state["rag_chat_menu"] = MENU_CHAT
    elif not is_logged_in() and current == MENU_SIGNUP:
        st.session_state["rag_chat_menu"] = MENU_CHAT


def render_page_menu() -> str:
    """Document Assistant sections — main area (keeps the app sidebar uncluttered)."""
    inject_document_assistant_styles()
    ensure_document_assistant_menu()
    st.caption("Document Assistant")
    menu_options = MENU_OPTIONS_SIGNED_IN if is_logged_in() else MENU_OPTIONS
    choice = st.radio(
        "Section",
        menu_options,
        key="rag_chat_menu",
        horizontal=True,
        label_visibility="collapsed",
    )
    user = current_user()
    if user:
        st.caption(
            f"Signed in as **{user.get('username', 'User')}** · {user.get('email', '')}"
        )
        if st.button("Sign out", key="rag_chat_logout", type="primary"):
            former_uid = resolve_portal_user_id()
            logout_user()
            set_demo_user(former_uid)
            st.session_state.portal_demo_user_select = former_uid
            st.session_state.pop(RAG_OPEN_SIGNIN_KEY, None)
            queue_auth_toast("You have been signed out.", "info")
            navigate_rag_menu(MENU_CHAT)
    st.divider()
    return choice


def render_sidebar_menu() -> str:
    """Backward-compatible alias — prefer :func:`render_page_menu`."""
    return render_page_menu()


def render_account_summary_panel() -> None:
    """Shown when already signed in on the auth tab."""
    user = current_user()
    if not user:
        return
    render_doc_hero(
        f"Signed in as {user.get('username', 'User')}",
        f"{user.get('email', '')} · Your session is active across the app until you sign out.",
        chip="Account active",
    )
    with st.container(key="doc_auth_panel"):
        section_heading("Your account", variant="plan")
        st.markdown(
            f"- **Username:** {user.get('username', '—')}  \n"
            f"- **Email:** {user.get('email', '—')}  \n"
            f"- **Member since:** {user.get('created_at', '—')}"
        )
        st.info("Open the **Chat** tab above to talk to the policy assistant.")
        chat_col, out_col = st.columns(2)
        with chat_col:
            if st.button("Go to Chat", type="primary", key="rag_goto_chat"):
                navigate_rag_menu(MENU_CHAT)
        with out_col:
            if st.button("Sign out", key="rag_account_sign_out"):
                former_uid = resolve_portal_user_id()
                logout_user()
                set_demo_user(former_uid)
                st.session_state.portal_demo_user_select = former_uid
                st.session_state.pop(RAG_OPEN_SIGNIN_KEY, None)
                queue_auth_toast("You have been signed out.", "info")
                navigate_rag_menu(MENU_CHAT)


def _login_email_prefill() -> str:
    from services.portal_user_context import effective_portal_profile

    uid = resolve_portal_user_id()
    profile = effective_portal_profile(uid)
    return str(profile.get("email") or "").strip()


def render_signup_signin_panel() -> None:
    if is_logged_in():
        render_account_summary_panel()
        return

    with st.container(key="doc_auth_panel"):
        st.markdown(
            polish_ui_copy(
                "Registration is **local to this machine** (demo). Use a fictional email."
            )
        )

        tab_reg, tab_login = st.tabs(["Sign up", "Sign in"])

        prefill_email = _login_email_prefill()
        if prefill_email and not st.session_state.get("rag_login_email"):
            st.session_state["rag_login_email"] = prefill_email

        with tab_reg:
            with st.form("rag_chat_register"):
                username = st.text_input("Username", placeholder="traveler_demo")
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                )
                password_confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    placeholder="Re-enter your password",
                )
                accept = st.checkbox(
                    "I have read the **Terms & Conditions** (sidebar → Terms & Conditions)",
                    value=False,
                )
                submitted = st.form_submit_button("Create account", type="primary")
                if submitted:
                    if not accept:
                        st.error("Please accept the Terms & Conditions before signing up.")
                    elif password != password_confirm:
                        st.error("Passwords do not match. Please re-enter them.")
                    else:
                        ok, msg = register_user(username, email, password)
                        if ok:
                            from services.portal_user_context import sync_portal_user_context

                            sync_portal_user_context()
                            st.session_state.pop(RAG_OPEN_SIGNIN_KEY, None)
                            set_rag_chat_menu(MENU_CHAT)
                            queue_auth_toast(msg.replace("**", ""), "success")
                            st.rerun()
                        else:
                            st.error(msg)

        with tab_login:
            with st.form("rag_chat_login"):
                email = st.text_input("Email", key="rag_login_email")
                password = st.text_input("Password", type="password", key="rag_login_password")
                submitted = st.form_submit_button("Sign in", type="primary")
                if submitted:
                    ok, msg = login_user(email, password)
                    if ok:
                        from services.portal_user_context import sync_portal_user_context

                        sync_portal_user_context()
                        st.session_state.pop(RAG_OPEN_SIGNIN_KEY, None)
                        set_rag_chat_menu(MENU_CHAT)
                        queue_auth_toast(msg.replace("**", ""), "success")
                        st.rerun()
                    else:
                        st.error(msg)


def render_welcome_banner() -> None:
    user = current_user()
    if not user:
        return
    render_doc_hero(
        f"Hi, {user.get('username', 'User')}",
        f"{user.get('email', '')} · Ask anything about terms, refunds, and packages.",
        chip="Grounded RAG · Sources on every reply",
    )


def render_full_terms() -> None:
    render_doc_hero(
        "Terms & Conditions",
        "Full platform notice — same content as Terms & Policies, organized in tabs.",
        chip="Read before you sign up",
    )
    with st.container(key="doc_terms_panel"):
        render_comprehensive_terms(show_platform_intro=False)
