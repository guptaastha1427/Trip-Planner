"""Shared policy / terms assistant chat (same engine as Help & Support bot)."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from services.rag_chat_auth import is_logged_in
from services.rag_citations import assistant_message_uses_html
from services.support_faq import answer_support_query
from services.ui_copy import polish_ui_copy
from services.website_rag import load_documents_from_url, validate_http_url

_FAB_KEY = "trip_policy_bot_fab_btn"
_POLICY_DIALOG_OPEN_KEY = "trip_policy_bot_dialog_open"


def _messages_key(user_id: str, session_key: str) -> str:
    return f"policy_bot_messages_{session_key}_{user_id}"


def _input_key(session_key: str) -> str:
    return f"policy_bot_input_{session_key}"


def _url_index_key(session_key: str) -> str:
    return f"policy_bot_url_index_{session_key}"


def _pending_query_key(user_id: str, session_key: str) -> str:
    return f"policy_bot_pending_{session_key}_{user_id}"


_TYPING_STYLES_KEY = "_policy_bot_typing_styles"


def inject_policy_chat_typing_styles() -> None:
    """One-time CSS for in-chat thinking indicator (three animated dots)."""
    if st.session_state.get(_TYPING_STYLES_KEY):
        return
    st.session_state[_TYPING_STYLES_KEY] = True
    st.markdown(
        """
        <style>
        .policy-bot-typing {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            min-height: 1.25rem;
            padding: 0.15rem 0;
        }
        .policy-bot-typing span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #7c6cf0;
            animation: policy-bot-dot-bounce 1.2s ease-in-out infinite;
        }
        .policy-bot-typing span:nth-child(2) { animation-delay: 0.15s; }
        .policy-bot-typing span:nth-child(3) { animation-delay: 0.3s; }
        @keyframes policy-bot-dot-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.45; }
            40% { transform: translateY(-6px); opacity: 1; }
        }
        a.rag-inline-cite {
            color: #5b57a6 !important;
            font-weight: 600;
            text-decoration: underline;
            text-underline-offset: 2px;
        }
        a.rag-inline-cite:hover {
            color: #6d28d9 !important;
        }
        span.rag-inline-cite {
            color: #5b57a6;
            font-weight: 600;
            border-bottom: 1px dotted rgba(91, 87, 166, 0.55);
            cursor: help;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_typing_indicator() -> None:
    inject_policy_chat_typing_styles()
    st.markdown(
        '<div class="policy-bot-typing" role="status" aria-live="polite" '
        'aria-label="Assistant is thinking"><span></span><span></span><span></span></div>',
        unsafe_allow_html=True,
    )


def _append_assistant_turn(
    mk: str,
    *,
    portal_user_id: str | None,
    user_id: str,
    query: str,
    escalate_page_hint: str,
) -> None:
    try:
        reply, escalate, sources = answer_support_query(
            portal_user_id or user_id,
            query,
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
            background: #3b82f6 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 0 #2563eb !important;
            cursor: pointer !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
        }}
        div.element-container.st-key-{_FAB_KEY} button:hover {{
            filter: brightness(1.1);
            transform: translateY(-1px);
            box-shadow: 0 6px 0 #2563eb !important;
        }}
        div.element-container.st-key-{_FAB_KEY} button:active {{
            filter: brightness(0.9);
            transform: translateY(2px);
            box-shadow: 0 2px 0 #2563eb !important;
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


def _render_chat_body(role: str, text: str) -> None:
    body = polish_ui_copy(text)
    if role == "assistant" and assistant_message_uses_html(body):
        st.markdown(body, unsafe_allow_html=True)
    else:
        st.markdown(body)


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
            "Retrieved sources appear as **inline citations** in each reply (hover for excerpts)."
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

    pk = _pending_query_key(user_id, session_key)
    inject_policy_chat_typing_styles()

    chat_panel = (
        st.container(key=chat_panel_key) if chat_panel_key else st.container()
    )
    with chat_panel:
        for msg in st.session_state[mk]:
            with st.chat_message(msg["role"]):
                _render_chat_body(msg["role"], msg["text"])

        # Keep chat_input before pending work so the bar stays mounted every run.
        prompt = st.chat_input(
            "Ask about terms, refunds, packages…",
            key=_input_key(session_key),
            disabled=bool(st.session_state.get(pk)),
        )
        if prompt:
            st.session_state[mk].append(
                {"role": "user", "text": prompt, "sources": []}
            )
            st.session_state[pk] = prompt
            st.rerun()

        pending = st.session_state.get(pk)
        if pending:
            with st.chat_message("assistant"):
                _render_typing_indicator()
                with st.spinner("Thinking…"):
                    _append_assistant_turn(
                        mk,
                        portal_user_id=portal_user_id,
                        user_id=user_id,
                        query=str(pending),
                        escalate_page_hint=escalate_page_hint,
                    )
            st.session_state.pop(pk, None)
            st.rerun()


def _dismiss_trip_policy_dialog() -> None:
    st.session_state[_POLICY_DIALOG_OPEN_KEY] = False


@st.dialog("Policy assistant", width="large", on_dismiss=_dismiss_trip_policy_dialog)
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
    if _POLICY_DIALOG_OPEN_KEY not in st.session_state:
        st.session_state[_POLICY_DIALOG_OPEN_KEY] = False

    if st.button(
        "🤖",
        key=_FAB_KEY,
        help="Policy & terms assistant",
        type="primary",
    ):
        st.session_state[_POLICY_DIALOG_OPEN_KEY] = True

    if st.session_state[_POLICY_DIALOG_OPEN_KEY]:
        _trip_planner_policy_dialog(user_id)


def render_sidebar_trip_policy_bot(user_id: str) -> None:
    with st.sidebar.popover("💬 Policy assistant", use_container_width=True):
        render_policy_bot_chat(
            user_id,
            session_key="trip_planner_sidebar",
            show_intro=True,
        )
