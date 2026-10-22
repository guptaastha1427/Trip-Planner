"""Document Assistant layout styles (presentation only)."""

from __future__ import annotations

import streamlit as st


def inject_document_assistant_styles() -> None:
    st.markdown(
        """
        <style>
        .doc-hero {
            background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 55%, #ede9fe 100%);
            border: 1px solid rgba(199, 210, 254, 0.75);
            border-radius: 28px;
            padding: 1.35rem 1.5rem;
            margin: 0 0 1rem 0;
            box-shadow: 0 18px 48px rgba(74, 71, 138, 0.12);
            transition: all 0.3s ease-in-out;
        }
        .doc-hero__title {
            font-size: 1.75rem;
            font-weight: 700;
            color: #1e1b4b;
            letter-spacing: -0.03em;
            margin: 0 0 0.35rem 0;
        }
        .doc-hero__sub {
            margin: 0;
            color: #64748b;
            font-size: 0.95rem;
            line-height: 1.55;
        }
        .doc-welcome-chip {
            display: inline-block;
            margin-top: 0.65rem;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            background: rgba(74, 71, 138, 0.1);
            border: 1px solid rgba(124, 108, 240, 0.35);
            color: #4a478a;
            font-size: 0.78rem;
            font-weight: 600;
        }

        section[data-testid="stSidebar"] [class*="st-key-rag_chat_menu"] label {
            background: #ffffff !important;
            border: 1px solid rgba(199, 210, 254, 0.7) !important;
            border-radius: 16px !important;
            padding: 0.55rem 0.65rem !important;
            margin-bottom: 0.35rem !important;
            color: #475569 !important;
            font-weight: 600 !important;
            transition: all 0.18s ease;
            box-shadow: 0 4px 14px rgba(74, 71, 138, 0.06);
        }
        section[data-testid="stSidebar"] [class*="st-key-rag_chat_menu"] label:hover {
            border-color: rgba(74, 71, 138, 0.35) !important;
            transform: translateY(-1px);
        }
        section[data-testid="stSidebar"] [class*="st-key-rag_chat_menu"] div[role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, #4a478a, #6d28d9) !important;
            border-color: transparent !important;
            color: #ffffff !important;
            box-shadow: 0 10px 24px rgba(74, 71, 138, 0.28);
        }

        [class*="st-key-doc_chat_panel"] {
            background: #ffffff !important;
            border: 1px solid rgba(199, 210, 254, 0.7) !important;
            border-radius: 26px !important;
            padding: 1rem 1.1rem 0.5rem !important;
            box-shadow: 0 16px 44px rgba(74, 71, 138, 0.1) !important;
            transition: box-shadow 0.2s ease;
        }
        [class*="st-key-doc_tools_panel"] {
            background: #ffffff !important;
            border: 1px solid rgba(199, 210, 254, 0.65) !important;
            border-radius: 24px !important;
            padding: 1rem 1rem !important;
            box-shadow: 0 12px 36px rgba(74, 71, 138, 0.08) !important;
        }
        [class*="st-key-doc_auth_panel"] {
            max-width: 520px;
            margin: 0 auto 1rem auto;
            background: #ffffff !important;
            border: 1px solid rgba(199, 210, 254, 0.7) !important;
            border-radius: 28px !important;
            padding: 1.25rem 1.35rem !important;
            box-shadow: 0 20px 56px rgba(74, 71, 138, 0.12);
        }
        [class*="st-key-doc_terms_panel"] {
            background: #ffffff !important;
            border: 1px solid rgba(199, 210, 254, 0.55) !important;
            border-radius: 24px !important;
            padding: 0.5rem 1rem 1rem !important;
            box-shadow: 0 12px 36px rgba(74, 71, 138, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_doc_hero(title: str, subtitle: str, chip: str | None = None) -> None:
    chip_html = f'<span class="doc-welcome-chip">{chip}</span>' if chip else ""
    st.markdown(
        f"""
        <div class="doc-hero">
            <p class="doc-hero__title">{title}</p>
            <p class="doc-hero__sub">{subtitle}</p>
            {chip_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
