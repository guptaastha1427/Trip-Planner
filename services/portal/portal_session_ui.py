"""Per-user Streamlit session keys for portal chat / forms."""

from __future__ import annotations

import streamlit as st


def clear_ephemeral_portal_ui() -> None:
    """Drop UI-only keys when switching demo user (data stays in portal JSON)."""
    for key in (
        "support_chat",
        "bot_messages",
        "bot_eval",
        "bot_booking",
        "last_eval",
        "last_eval_booking",
    ):
        st.session_state.pop(key, None)


def support_chat_key(user_id: str) -> str:
    return f"support_chat_{user_id}"


def bot_messages_key(user_id: str) -> str:
    return f"bot_messages_{user_id}"


def bot_eval_key(user_id: str) -> str:
    return f"bot_eval_{user_id}"


def bot_booking_key(user_id: str) -> str:
    return f"bot_booking_{user_id}"


def bot_eval_ctx_key(user_id: str) -> str:
    return f"bot_eval_ctx_{user_id}"
