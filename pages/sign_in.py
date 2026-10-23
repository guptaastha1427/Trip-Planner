"""Sign in — local session for policy chat."""

from __future__ import annotations

import streamlit as st

from services.portal_ui import portal_page_setup
from services.portal_user_context import effective_portal_profile, resolve_portal_user_id, sync_portal_user_context
from services.rag_chat_auth import (
    current_user,
    init_rag_auth_session,
    is_logged_in,
    login_user,
    logout_user,
    mount_rag_auth_cookie_component,
    queue_auth_toast,
    render_auth_toasts,
)
from services.rag_chat_layout import inject_document_assistant_styles, render_doc_hero
from services.role_dashboard import PAGE_SUPPORT


def _login_email_prefill() -> str:
    uid = resolve_portal_user_id()
    profile = effective_portal_profile(uid)
    return str(profile.get("email") or "").strip()


def render() -> None:
    mount_rag_auth_cookie_component()
    init_rag_auth_session()
    sync_portal_user_context()
    inject_document_assistant_styles()
    portal_page_setup(
        "Sign in",
        "Sign in to use policy chat across the app.",
        page_kind=PAGE_SUPPORT,
    )
    render_auth_toasts()

    if is_logged_in():
        user = current_user() or {}
        render_doc_hero(
            f"Signed in as {user.get('username', 'User')}",
            str(user.get("email") or ""),
            chip="Session active",
        )
        if st.button("Sign out", key="sign_in_page_sign_out", type="primary"):
            logout_user()
            queue_auth_toast("You have been signed out.", "info")
            st.rerun()
        return

    render_doc_hero(
        "Sign in",
        "Use your local demo account email and password.",
        chip="Saved on this device",
    )
    prefill_email = _login_email_prefill()
    if prefill_email and not st.session_state.get("rag_login_email"):
        st.session_state["rag_login_email"] = prefill_email

    with st.form("sign_in_page_login"):
        email = st.text_input("Email", key="rag_login_email")
        password = st.text_input("Password", type="password", key="rag_login_password")
        submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            ok, msg = login_user(email, password)
            if ok:
                sync_portal_user_context()
                queue_auth_toast(msg.replace("**", ""), "success")
                st.rerun()
            else:
                st.error(msg)


render()
