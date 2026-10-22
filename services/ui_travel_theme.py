"""Light pastel / indigo travel UI theme — presentation only."""

from __future__ import annotations

import streamlit as st


def inject_travel_light_theme() -> None:
    st.markdown(
        """
        <style>
        @keyframes tpFadeUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes tpSoftPulse {
            0%, 100% { box-shadow: 0 10px 28px rgba(74, 71, 138, 0.28); }
            50% { box-shadow: 0 14px 36px rgba(74, 71, 138, 0.42); }
        }
        @keyframes tpExpandIn {
            from { opacity: 0.6; }
            to { opacity: 1; }
        }
        @keyframes tpTabIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes tpViewIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        :root {
            --tp-purple-700: #4a478a;
            --tp-purple-600: #5b57a6;
            --tp-purple-500: #7c6cf0;
            --tp-lavender-50: #f5f3ff;
            --tp-lavender-100: #ede9fe;
            --tp-card: #ffffff;
            --tp-card-border: rgba(199, 210, 254, 0.65);
            --tp-shadow: 0 14px 40px rgba(74, 71, 138, 0.1);
            --tp-radius-xl: 28px;
            --tp-radius-lg: 22px;
            --tp-radius-md: 18px;
            --tp-ink-950: #1e1b4b;
            --tp-ink-700: #475569;
            --tp-ink-500: #64748b;
        }

        html, body, .stApp, [data-testid="stAppViewContainer"] {
            background-color: #eef2ff !important;
            color: #334155 !important;
        }

        [data-testid="stMainBlockContainer"].block-container,
        section.main .block-container {
            --tp-main-gutter: 1.25rem;
            padding-top: var(--tp-main-gutter) !important;
            padding-left: var(--tp-main-gutter) !important;
            padding-right: var(--tp-main-gutter) !important;
            max-width: 1100px !important;
            margin-top: 0 !important;
        }

        /* Tabs & sections — transition only (no rerun flash on whole page) */
        [data-testid="stTabs"] [data-baseweb="tab-list"] button {
            transition: all 0.3s ease-in-out !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab-panel"],
        [data-baseweb="tab-panel"] {
            transition: opacity 0.3s ease-in-out, transform 0.3s ease-in-out;
        }
        section[data-testid="stSidebar"] [role="radiogroup"] label,
        section[data-testid="stSidebar"] nav a,
        section.main [role="radiogroup"] label {
            transition: all 0.3s ease-in-out;
        }
        [class*="st-key-doc_chat_panel"],
        [class*="st-key-doc_tools_panel"],
        [class*="st-key-doc_auth_panel"],
        [class*="st-key-doc_terms_panel"] {
            transition: all 0.3s ease-in-out;
        }

        /* RAG source reference cards (chat) */
        .rag-source-block {
            background: #fafbff;
            border: 1px solid rgba(199, 210, 254, 0.85);
            border-radius: 14px;
            padding: 0.65rem 0.85rem;
            margin: 0.4rem 0 0.55rem 0;
            box-shadow: 0 6px 18px rgba(74, 71, 138, 0.07);
            transition: all 0.3s ease-in-out;
        }
        .rag-source-block:hover {
            box-shadow: 0 10px 24px rgba(74, 71, 138, 0.11);
            transform: translateY(-1px);
        }
        .rag-source-block__title {
            font-size: 0.82rem;
            font-weight: 700;
            color: #4a478a;
            margin: 0 0 0.35rem 0;
        }
        .rag-source-block__meta {
            font-size: 0.72rem;
            color: #64748b;
            margin: 0 0 0.35rem 0;
        }
        .rag-source-block__snippet {
            font-size: 0.8rem;
            line-height: 1.5;
            color: #334155;
            margin: 0;
            white-space: pre-wrap;
        }

        section.main h1, section.main h2, section.main h3, section.main h4,
        .trip-h, .trip-h--plan, .trip-h--itinerary, .trip-h--map, .trip-h--travel {
            color: var(--tp-ink-950) !important;
        }
        .trip-h--plan { color: var(--tp-purple-700) !important; }
        .trip-h--travel { color: #6d28d9 !important; }
        section.main [data-testid="stMarkdownContainer"] a {
            color: var(--tp-purple-600) !important;
        }

        /* Floating white cards */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--tp-card) !important;
            border: 1px solid var(--tp-card-border) !important;
            border-radius: var(--tp-radius-lg) !important;
            box-shadow: var(--tp-shadow) !important;
            transition: all 0.3s ease-in-out;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 48px rgba(74, 71, 138, 0.14) !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stVerticalBlockBorderWrapper"] {
            background: #fafbff !important;
            border-color: #e8eeff !important;
        }

        details[data-testid="stExpander"] {
            background: var(--tp-card) !important;
            border: 1px solid var(--tp-card-border) !important;
            border-radius: var(--tp-radius-md) !important;
            box-shadow: 0 8px 24px rgba(74, 71, 138, 0.08);
            transition: all 0.3s ease-in-out;
        }
        details[data-testid="stExpander"][open] {
            box-shadow: 0 12px 32px rgba(74, 71, 138, 0.12);
        }
        details[data-testid="stExpander"] summary {
            color: var(--tp-ink-950) !important;
            font-weight: 600 !important;
        }

        [data-testid="stAlert"] {
            background: #ffffff !important;
            border: 1px solid var(--tp-card-border) !important;
            border-radius: var(--tp-radius-md) !important;
            box-shadow: var(--tp-shadow);
            transition: all 0.3s ease-in-out;
        }

        /* Chat cards */
        [data-testid="stChatMessage"] {
            background: #ffffff !important;
            border: 1px solid var(--tp-card-border) !important;
            border-radius: var(--tp-radius-md) !important;
            padding: 0.8rem 1rem !important;
            margin-bottom: 0.75rem !important;
            box-shadow: 0 10px 28px rgba(74, 71, 138, 0.08) !important;
            transition: all 0.3s ease-in-out;
        }
        [data-testid="stChatMessage"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 34px rgba(74, 71, 138, 0.12) !important;
        }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li {
            color: #334155 !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            border-color: rgba(124, 108, 240, 0.35) !important;
            background: linear-gradient(180deg, #ffffff, #faf5ff) !important;
        }
        [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
            border-color: rgba(167, 139, 250, 0.4) !important;
        }

        [data-testid="stChatInput"] > div {
            background: #ffffff !important;
            border: 1px solid var(--tp-card-border) !important;
            border-radius: 999px !important;
            box-shadow: 0 8px 22px rgba(74, 71, 138, 0.1);
            transition: all 0.3s ease-in-out;
        }
        [data-testid="stChatInput"] > div:focus-within {
            border-color: rgba(74, 71, 138, 0.45) !important;
            box-shadow: 0 10px 28px rgba(74, 71, 138, 0.16);
        }
        [data-testid="stChatInput"] textarea {
            color: #1e293b !important;
        }

        /* Indigo pill buttons — "Let's Go!" style */
        .stButton button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        [data-testid="stFormSubmitButton"] button {
            border-radius: 999px !important;
            background: linear-gradient(135deg, #4a478a 0%, #5b57a6 55%, #6d28d9 100%) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 10px 28px rgba(74, 71, 138, 0.32) !important;
            transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease !important;
        }
        .stButton button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover,
        [data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-2px) scale(1.01);
            filter: brightness(1.04);
            animation: tpSoftPulse 1.6s ease-in-out infinite;
        }

        .stButton button[kind="secondary"],
        button[data-testid="stBaseButton-secondary"] {
            border-radius: 16px !important;
            background: #ffffff !important;
            color: var(--tp-purple-700) !important;
            border: 1px solid var(--tp-card-border) !important;
            box-shadow: 0 4px 14px rgba(74, 71, 138, 0.06);
            transition: all 0.18s ease;
        }
        .stButton button[kind="secondary"]:hover {
            border-color: rgba(74, 71, 138, 0.35) !important;
            background: #f5f3ff !important;
        }

        section.main input[data-testid="stTextInputField"],
        section.main .block-container input[data-testid="stTextInputField"],
        section.main textarea,
        section.main .block-container textarea,
        section.main [data-baseweb="select"] > div,
        section.main .block-container [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] input[data-testid="stTextInputField"],
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 14px !important;
            transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        section.main input:focus, section.main textarea:focus,
        section[data-testid="stSidebar"] input:focus {
            border-color: rgba(74, 71, 138, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(124, 108, 240, 0.18) !important;
        }

        .hint-card, .dest-guide-card, .weather-card, .travel-tips-card,
        .trip-stats__cell {
            background: #ffffff !important;
            border: 1px solid var(--tp-card-border) !important;
            box-shadow: var(--tp-shadow) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hint-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 18px 44px rgba(74, 71, 138, 0.14) !important;
        }

        [data-baseweb="tab-list"] {
            background: #ffffff;
            border-radius: 16px;
            padding: 0.3rem;
            border: 1px solid var(--tp-card-border);
            box-shadow: 0 6px 18px rgba(74, 71, 138, 0.06);
        }
        [data-baseweb="tab"][aria-selected="true"] {
            color: var(--tp-purple-700) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(124, 108, 240, 0.12) !important;
            color: var(--tp-purple-700) !important;
        }

        .portal-hero {
            background: linear-gradient(135deg, #4a478a 0%, #7c3aed 48%, #a78bfa 120%) !important;
            border: none !important;
            box-shadow: 0 20px 50px rgba(74, 71, 138, 0.25) !important;
        }
        .portal-hero h1, .portal-hero p { color: #ffffff !important; }

        [data-testid="stPopover"] > button {
            border-radius: 14px !important;
            background: #ffffff !important;
            border: 1px solid var(--tp-card-border) !important;
            color: var(--tp-purple-700) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
