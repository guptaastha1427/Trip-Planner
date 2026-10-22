"""UI helpers for Document & Policy Assistant (auth, terms, navigation)."""

from __future__ import annotations

import streamlit as st

from services.rag_chat_auth import (
    current_user,
    is_logged_in,
    login_user,
    logout_user,
    register_user,
)
from services.rag_chat_layout import inject_document_assistant_styles, render_doc_hero
from services.terms_page_ui import render_comprehensive_terms
from services.ui_components import section_heading
from services.ui_copy import polish_ui_copy

MENU_SIGNUP = "Sign up / Sign in"
MENU_CHAT = "Chat"
MENU_TERMS = "Terms & Conditions"

MENU_OPTIONS = (MENU_SIGNUP, MENU_CHAT, MENU_TERMS)


def render_page_menu() -> str:
    """Document Assistant sections — main area (keeps the app sidebar uncluttered)."""
    inject_document_assistant_styles()
    st.caption("Document Assistant")
    choice = st.radio(
        "Section",
        MENU_OPTIONS,
        key="rag_chat_menu",
        horizontal=True,
        label_visibility="collapsed",
    )
    user = current_user()
    if user:
        st.caption(
            f"Signed in as **{user.get('username', 'User')}** · {user.get('email', '')}"
        )
        if st.button("Sign out", key="rag_chat_logout"):
            logout_user()
            st.session_state["rag_chat_menu"] = MENU_SIGNUP
            st.rerun()
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
        if st.button("Go to Chat", type="primary", key="rag_goto_chat"):
            st.session_state["rag_chat_menu"] = MENU_CHAT
            st.rerun()


def render_signup_signin_panel() -> None:
    if is_logged_in():
        render_account_summary_panel()
        return

    render_doc_hero(
        "Welcome",
        "Create a local account to unlock grounded policy chat.",
        chip="Free · Saved on this machine · No real payments",
    )
    with st.container(key="doc_auth_panel"):
        section_heading("Create an account or sign in", variant="plan")
        st.markdown(
            polish_ui_copy(
                "Registration is **local to this machine** (demo). Use a fictional email."
            )
        )

        tab_reg, tab_login = st.tabs(["Sign up", "Sign in"])

        with tab_reg:
            with st.form("rag_chat_register"):
                username = st.text_input("Username", placeholder="traveler_demo")
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="At least 8 characters",
                )
                accept = st.checkbox(
                    "I have read the **Terms & Conditions** (sidebar → Terms & Conditions)",
                    value=False,
                )
                submitted = st.form_submit_button("Create account", type="primary")
                if submitted:
                    if not accept:
                        st.error("Please accept the Terms & Conditions before signing up.")
                    else:
                        ok, msg = register_user(username, email, password)
                        if ok:
                            st.session_state["rag_chat_menu"] = MENU_CHAT
                            st.success(msg)
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
                        st.session_state["rag_chat_menu"] = MENU_CHAT
                        st.success(msg)
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
