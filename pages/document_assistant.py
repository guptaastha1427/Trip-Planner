"""Document & Policy Assistant — signup, terms, and gated RAG chat."""

from __future__ import annotations

import streamlit as st

from services.policy_bot_ui import render_policy_bot_chat, render_url_indexer_panel
from services.portal_ui import portal_page_setup
from services.rag_chat_auth import chat_user_id, current_user, is_logged_in
from services.rag_chat_layout import inject_document_assistant_styles, render_doc_hero
from services.rag_chat_ui import (
    MENU_CHAT,
    MENU_SIGNUP,
    MENU_TERMS,
    render_full_terms,
    render_page_menu,
    render_signup_signin_panel,
    render_welcome_banner,
)
from services.role_dashboard import PAGE_SUPPORT

_SESSION_KEY = "document_assistant"


def render() -> None:
    inject_document_assistant_styles()
    portal_page_setup(
        "Document & Policy Assistant",
        "Sign up, read terms, and chat with a grounded policy RAG bot.",
        page_kind=PAGE_SUPPORT,
    )

    menu = render_page_menu()

    if menu == MENU_SIGNUP:
        render_signup_signin_panel()
        return

    if menu == MENU_TERMS:
        render_full_terms()
        return

    # Chat — two-column layout: conversation + tools
    if not is_logged_in():
        render_doc_hero(
            "Policy chat",
            "Sign in to start a grounded conversation with retrieved sources.",
            chip="Login required",
        )
        st.warning(
            "Create an account or sign in under **Sign up / Sign in** above."
        )
        render_signup_signin_panel()
        return

    render_welcome_banner()
    demo_uid = st.session_state.get("demo_user_id") or "user-1"

    chat_col, tools_col = st.columns([1.65, 1], gap="large")

    with tools_col:
        with st.container(key="doc_tools_panel"):
            st.markdown("**Tools & context**")
            render_url_indexer_panel(_SESSION_KEY, compact=True)
            st.divider()
            auth = current_user()
            if auth:
                st.caption("**Your app account** (policy chat)")
                st.markdown(
                    f"**{auth.get('username', 'User')}** · `{auth.get('email', '')}`"
                )
            st.caption("**Booking preview profile** (sample refunds & tickets)")
            st.markdown(f"`{demo_uid}`")
            st.caption("Change the booking preview from the profile control at the bottom of the sidebar.")

    with chat_col:
        render_policy_bot_chat(
            chat_user_id(),
            portal_user_id=demo_uid,
            session_key=_SESSION_KEY,
            show_intro=True,
            escalate_page_hint="**Help & Support → My tickets**",
            show_url_indexer=True,
            url_indexer_in_tools_panel=True,
            require_login=True,
            chat_panel_key="doc_chat_panel",
        )


render()
