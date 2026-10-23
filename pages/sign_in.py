"""Sign in — local session for policy chat."""

from __future__ import annotations

from services.portal_ui import portal_page_setup
from services.portal_user_context import sync_portal_user_context
from services.rag_chat_auth import (
    init_rag_auth_session,
    mount_rag_auth_cookie_component,
    render_auth_toasts,
)
from services.rag_chat_ui import render_signup_signin_panel
from services.role_dashboard import PAGE_SUPPORT

SIGN_IN_PAGE_PATH = "pages/sign_in.py"


def render() -> None:
    mount_rag_auth_cookie_component()
    init_rag_auth_session()
    sync_portal_user_context()
    portal_page_setup(
        "Sign in",
        "Create an account or sign in to use policy chat across the app.",
        page_kind=PAGE_SUPPORT,
    )
    render_auth_toasts()
    render_signup_signin_panel()


render()
