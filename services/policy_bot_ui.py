"""Shared policy / terms assistant chat (same engine as Help & Support bot)."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from services.rag_chat_auth import is_logged_in
from services.support_faq import answer_support_query
from services.ui_copy import polish_ui_copy
from services.website_rag import load_documents_from_url, validate_http_url

_FAB_KEY = "trip_policy_bot_fab_btn"


def _messages_key(user_id: str, session_key: str) -> str:
    return f"policy_bot_messages_{session_key}_{user_id}"


def _input_key(session_key: str) -> str:
    return f"policy_bot_input_{session_key}"


def _url_index_key(session_key: str) -> str:
    return f"policy_bot_url_index_{session_key}"


def inject_policy_bot_fab_styles() -> None:
    st.markdown(
        f"""
        <style>
        div.element-container.st-key-{_FAB_KEY},
        [class*="st-key-{_FAB_KEY}"] {{
            position: fixed !important;
            bottom: 1.35rem !important;
            right: 1.35rem !important;
            z-index: 100000 !important;
            width: auto !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        div.element-container.st-key-{_FAB_KEY} button,
        [class*="st-key-{_FAB_KEY}"] button {{
            min-width: 3.5rem !important;
            min-height: 3.5rem !important;
            width: 3.5rem !important;
            height: 3.5rem !important;
            padding: 0 !important;
            border-radius: 999px !important;
            border: none !important;
            font-size: 1.55rem !important;
            line-height: 1 !important;
            background: linear-gradient(135deg, #4a478a 0%, #5b57a6 55%, #6d28d9 100%) !important;
            color: #ffffff !important;
            box-shadow: 0 10px 32px rgba(74, 71, 138, 0.38),
                0 4px 12px rgba(109, 40, 217, 0.25) !important;
            cursor: pointer !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
        }}
        div.element-container.st-key-{_FAB_KEY} button:hover {{
            filter: brightness(1.08);
            transform: scale(1.06) translateY(-2px);
            box-shadow: 0 14px 40px rgba(34, 211, 238, 0.55),
                0 6px 16px rgba(20, 184, 166, 0.4) !important;
        }}
        div.element-container.st-key-{_FAB_KEY} button p {{
            color: #ffffff !important;
            margin: 0 !important;
            font-size: 1.55rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_url_indexer_panel(session_key: str, *, compact: bool = False) -> None:
    """URL scrape test UI (same logic as in-chat expander)."""
    if compact:
        st.caption("Validate a public page for the web RAG pipeline.")
    else:
        st.markdown("**URL scrape test**")
        st.caption(
            "Checks that a public page can be scraped and chunked. "
            "Policy answers still use the in-app Terms index."
        )
    url = st.text_input(
        "Website URL",
        key=f"policy_url_{session_key}",
        placeholder="https://…",
    )
    if st.button("Test URL scrape", key=f"policy_url_btn_{session_key}", type="primary"):
        ok, normalized = validate_http_url(url)
        if not ok:
            st.error(normalized)
        else:
            docs, err = load_documents_from_url(normalized)
            if err:
                st.warning(err)
            else:
                st.session_state[_url_index_key(session_key)] = normalized
                st.success(
                    f"Loaded **{len(docs)}** chunks (index with **GEMINI_API_KEY** in `.env`)."
                )


def _render_sources(sources: List[Dict[str, Any]]) -> None:
    """Retrieved chunks as accordions under each assistant reply."""
    if not sources:
        return
    st.markdown("**Grounded references**")
    st.caption(
        "Expand a reference to see the exact excerpt used before the answer was generated."
    )
    for i, src in enumerate(sources, 1):
        label = polish_ui_copy(str(src.get("source") or f"Document chunk {i}"))
        snippet = polish_ui_copy(str(src.get("text") or ""))
        score = src.get("score")
        title = f"Reference {i} — {label}"
        with st.expander(title, expanded=False):
            if score is not None:
                st.caption(f"Similarity score: {score}")
            else:
                st.caption("Retrieved from policy index")
            st.markdown(snippet)


def render_policy_bot_chat(
    user_id: str,
    *,
    portal_user_id: str | None = None,
    session_key: str,
    show_intro: bool = True,
    escalate_page_hint: str = "**Help & Support → My tickets**",
    show_url_indexer: bool = False,
    url_indexer_in_tools_panel: bool = False,
    require_login: bool = False,
    login_hint: str = "Open **Document Assistant** in the sidebar → **Sign up / Sign in**.",
    chat_panel_key: str | None = None,
) -> None:
    if require_login and not is_logged_in():
        st.warning(
            polish_ui_copy(
                f"Please sign in to use the policy chat. {login_hint}"
            )
        )
        return

    if show_intro:
        st.caption(
            "Answers from **Terms & Conditions & Policies** (and your account when relevant). "
            "Each reply includes **grounded references** — expand each accordion to verify excerpts."
        )

    if show_url_indexer and not url_indexer_in_tools_panel:
        with st.expander("Optional: validate an external policy URL", expanded=False):
            render_url_indexer_panel(session_key)

    mk = _messages_key(user_id, session_key)
    if mk not in st.session_state:
        st.session_state[mk] = [
            {
                "role": "assistant",
                "text": (
                    "Hi! I can explain **terms, refunds, packages, bookings, and account rules**. "
                    "What would you like to know?"
                ),
                "sources": [],
            }
        ]

    chat_panel = (
        st.container(key=chat_panel_key) if chat_panel_key else st.container()
    )
    with chat_panel:
        for msg in st.session_state[mk]:
            with st.chat_message(msg["role"]):
                st.markdown(polish_ui_copy(msg["text"]))
                if msg["role"] == "assistant":
                    _render_sources(msg.get("sources") or [])

        prompt = st.chat_input(
            "Ask about terms, refunds, packages…",
            key=_input_key(session_key),
        )
        if prompt:
            st.session_state[mk].append({"role": "user", "text": prompt, "sources": []})
            try:
                reply, escalate, sources = answer_support_query(
                    portal_user_id or user_id,
                    prompt,
                )
            except Exception as exc:
                reply = polish_ui_copy(
                    "I couldn't complete that search right now. "
                    "Check **GEMINI_API_KEY** and try "
                    "**GEMINI_EMBEDDING_MODEL=gemini-embedding-001** in `.env`, "
                    "then restart Streamlit. "
                    f"({type(exc).__name__})"
                )
                escalate, sources = True, []
            st.session_state[mk].append(
                {"role": "assistant", "text": reply, "sources": sources}
            )
            if escalate:
                st.session_state[mk].append(
                    {
                        "role": "assistant",
                        "text": f"For more help, open a support ticket under {escalate_page_hint}.",
                        "sources": [],
                    }
                )
            st.rerun()


@st.dialog("Policy assistant", width="large")
def _trip_planner_policy_dialog(user_id: str) -> None:
    render_policy_bot_chat(
        user_id,
        session_key="trip_planner",
        show_intro=True,
        escalate_page_hint="**Help & Support → My tickets**",
    )


def mount_trip_planner_policy_bot_styles() -> None:
    inject_policy_bot_fab_styles()


def render_trip_planner_policy_bot_fab(user_id: str) -> None:
    if st.button(
        "🤖",
        key=_FAB_KEY,
        help="Policy & terms assistant",
        type="primary",
    ):
        _trip_planner_policy_dialog(user_id)


def render_sidebar_trip_policy_bot(user_id: str) -> None:
    with st.sidebar.popover("💬 Policy assistant", use_container_width=True):
        render_policy_bot_chat(
            user_id,
            session_key="trip_planner_sidebar",
            show_intro=True,
        )
