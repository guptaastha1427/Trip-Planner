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
            --tp-nav-chip-active: #1d4ed8;
            --tp-nav-chip-line: #2563eb;
            --tp-nav-chip-rail: #e8eeff;
            --tp-btn-face: #3b82f6;
            --tp-btn-edge: #2563eb;
            --tp-btn-radius: 0.5rem;
            --tp-btn-edge-width: 4px;
        }

        /* === tp-nav-chip — reusable tab / section chip (curved underline) === */
        .tp-nav-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.85rem;
            align-items: flex-end;
            padding-bottom: 0.55rem;
            border-bottom: 2px solid var(--tp-nav-chip-rail);
            margin-bottom: 0.75rem;
        }
        .tp-nav-chip {
            position: relative;
            display: inline-block;
            font-size: 0.875rem;
            font-weight: 600;
            line-height: 1.25;
            color: var(--tp-ink-500);
            padding: 0.2rem 0.2rem 0.6rem;
            background: transparent;
            border: none;
            border-radius: 0;
        }
        .tp-nav-chip--active {
            color: var(--tp-nav-chip-active);
        }
        .tp-nav-chip--active::after {
            content: "";
            position: absolute;
            left: 10%;
            right: 10%;
            bottom: 0;
            height: 4px;
            background: var(--tp-nav-chip-line);
            border-radius: 50%;
            transform: scaleY(0.5);
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
            padding-bottom: 1.5rem !important;
            max-width: 1100px !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: 0 !important;
            box-sizing: border-box !important;
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

        /* 3D tactile buttons — Streamlit 1.55 nests <button> inside [data-testid="stButton"] */
        .stApp [data-testid="stButton"] button,
        .stApp .stButton button,
        .stApp button[data-testid="stBaseButton-PRIMARY"],
        .stApp button[data-testid="stBaseButton-SECONDARY"],
        .stApp button[data-testid="stBaseButton-TERTIARY"],
        .stApp button[data-testid="stBaseButton-PRIMARY_FORM_SUBMIT"],
        .stApp button[data-testid="stBaseButton-SECONDARY_FORM_SUBMIT"],
        .stApp button[data-testid="stBaseButton-TERTIARY_FORM_SUBMIT"],
        .stApp button[data-testid="stBaseButton-primary"],
        .stApp button[data-testid="stBaseButton-secondary"],
        .stApp [data-testid="stFormSubmitButton"] button,
        .stApp [data-testid="stDownloadButton"] button,
        .stApp [data-testid="stLinkButton"] a,
        .stApp [data-testid="stLinkButton"] button,
        .stApp [data-testid="stPopover"] button {
            text-decoration: none !important;
            cursor: pointer !important;
            font-weight: 600 !important;
            border-radius: var(--tp-btn-radius) !important;
            background: var(--tp-btn-face) !important;
            background-color: var(--tp-btn-face) !important;
            color: #ffffff !important;
            border: 1px solid var(--tp-btn-edge) !important;
            border-color: var(--tp-btn-edge) !important;
            border-bottom-width: var(--tp-btn-edge-width) !important;
            border-bottom-color: var(--tp-btn-edge) !important;
            box-shadow: none !important;
            transition:
                transform 0.15s ease,
                filter 0.15s ease,
                border-bottom-width 0.15s ease,
                background 0.15s ease,
                background-color 0.15s ease !important;
        }
        .stApp [data-testid="stButton"] button p,
        .stApp .stButton button p,
        .stApp [data-testid="stFormSubmitButton"] button p,
        .stApp [data-testid="stDownloadButton"] button p,
        .stApp [data-testid="stLinkButton"] a p,
        .stApp [data-testid="stLinkButton"] button p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        .stApp [data-testid="stButton"] button:hover:not(:disabled),
        .stApp .stButton button:hover:not(:disabled),
        .stApp button[data-testid="stBaseButton-PRIMARY"]:hover:not(:disabled),
        .stApp button[data-testid="stBaseButton-SECONDARY"]:hover:not(:disabled),
        .stApp button[data-testid="stBaseButton-TERTIARY"]:hover:not(:disabled),
        .stApp button[data-testid="stBaseButton-PRIMARY_FORM_SUBMIT"]:hover:not(:disabled),
        .stApp button[data-testid="stBaseButton-SECONDARY_FORM_SUBMIT"]:hover:not(:disabled),
        .stApp button[data-testid="stBaseButton-TERTIARY_FORM_SUBMIT"]:hover:not(:disabled),
        .stApp [data-testid="stFormSubmitButton"] button:hover:not(:disabled),
        .stApp [data-testid="stDownloadButton"] button:hover:not(:disabled),
        .stApp [data-testid="stLinkButton"] a:hover,
        .stApp [data-testid="stLinkButton"] button:hover:not(:disabled),
        .stApp [data-testid="stPopover"] button:hover:not(:disabled) {
            filter: brightness(1.1) !important;
            transform: translateY(-1px) !important;
            border-bottom-width: 6px !important;
            background-color: var(--tp-btn-face) !important;
        }
        .stApp [data-testid="stButton"] button:active:not(:disabled),
        .stApp .stButton button:active:not(:disabled),
        .stApp button[data-testid="stBaseButton-PRIMARY"]:active:not(:disabled),
        .stApp button[data-testid="stBaseButton-SECONDARY"]:active:not(:disabled),
        .stApp button[data-testid="stBaseButton-TERTIARY"]:active:not(:disabled),
        .stApp button[data-testid="stBaseButton-PRIMARY_FORM_SUBMIT"]:active:not(:disabled),
        .stApp button[data-testid="stBaseButton-SECONDARY_FORM_SUBMIT"]:active:not(:disabled),
        .stApp button[data-testid="stBaseButton-TERTIARY_FORM_SUBMIT"]:active:not(:disabled),
        .stApp [data-testid="stFormSubmitButton"] button:active:not(:disabled),
        .stApp [data-testid="stDownloadButton"] button:active:not(:disabled),
        .stApp [data-testid="stLinkButton"] a:active,
        .stApp [data-testid="stLinkButton"] button:active:not(:disabled),
        .stApp [data-testid="stPopover"] button:active:not(:disabled) {
            filter: brightness(0.9) !important;
            transform: translateY(2px) !important;
            border-bottom-width: 2px !important;
            background-color: var(--tp-btn-face) !important;
        }
        .stApp [data-testid="stButton"] button:disabled,
        .stApp [data-testid="stButton"] button[disabled],
        .stApp .stButton button:disabled,
        .stApp [data-testid="stFormSubmitButton"] button:disabled {
            opacity: 0.55 !important;
            cursor: not-allowed !important;
            transform: none !important;
            filter: none !important;
        }
        .stApp [data-testid="stButton"] button:focus-visible,
        .stApp [data-testid="stFormSubmitButton"] button:focus-visible,
        .stApp [data-testid="stDownloadButton"] button:focus-visible,
        .stApp [data-testid="stLinkButton"] a:focus-visible,
        .stApp [data-testid="stLinkButton"] button:focus-visible,
        .stApp [data-testid="stPopover"] button:focus-visible {
            outline: 2px solid #93c5fd !important;
            outline-offset: 2px !important;
            box-shadow: none !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarNavViewButton"] button {
            background: transparent !important;
            border: none !important;
            border-bottom-width: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            color: inherit !important;
            transform: none !important;
            filter: none !important;
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

        [data-baseweb="tab-border"],
        [data-baseweb="tab-highlight"] {
            display: none !important;
        }
        /* Streamlit tabs — frosted glass pills (all pages) */
        [data-testid="stTabs"] [data-baseweb="tab-list"] {
            background: transparent !important;
            border: none !important;
            border-bottom: none !important;
            box-shadow: none !important;
            gap: 0.25rem 1.35rem !important;
            padding: 0.2rem 0 0.85rem 0 !important;
            align-items: center !important;
            flex-wrap: wrap !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"],
        [data-testid="stTabs"] button[role="tab"] {
            font-family: var(--tp-font) !important;
            background: transparent !important;
            background-color: transparent !important;
            color: #1e293b !important;
            font-size: 0.9375rem !important;
            font-weight: 600 !important;
            line-height: 1.25 !important;
            padding: 0.45rem 1.05rem !important;
            margin: 0 !important;
            border: 1px solid transparent !important;
            border-radius: 999px !important;
            box-shadow: none !important;
            min-height: unset !important;
            display: inline-flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: center !important;
            transform: none !important;
            filter: none !important;
            transition:
                background 0.2s ease,
                background-color 0.2s ease,
                border-color 0.2s ease,
                box-shadow 0.2s ease !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"] p,
        [data-testid="stTabs"] button[role="tab"] p {
            margin: 0 !important;
            color: inherit !important;
            font-weight: inherit !important;
            line-height: 1.25 !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"]::after,
        [data-testid="stTabs"] button[role="tab"]::after {
            display: none !important;
            content: none !important;
            visibility: hidden !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
        [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            background: rgba(255, 255, 255, 0.72) !important;
            background-color: rgba(255, 255, 255, 0.72) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            backdrop-filter: blur(12px) !important;
            border-color: rgba(199, 210, 254, 0.65) !important;
            box-shadow: 0 4px 14px rgba(74, 71, 138, 0.1) !important;
            color: #1e293b !important;
        }
        [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="false"]:hover,
        [data-testid="stTabs"] button[role="tab"][aria-selected="false"]:hover {
            background: rgba(255, 255, 255, 0.45) !important;
            background-color: rgba(255, 255, 255, 0.45) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            backdrop-filter: blur(10px) !important;
            border-color: rgba(199, 210, 254, 0.4) !important;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: rgba(124, 108, 240, 0.12) !important;
            color: var(--tp-purple-700) !important;
        }

        .portal-hero-wrap {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
        }
        .portal-hero {
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            border: none !important;
            box-shadow: 0 12px 32px rgba(74, 71, 138, 0.18) !important;
        }
        .portal-hero h1, .portal-hero p { color: #ffffff !important; }


        /* Package detail — catalog & booking */
        .pkg-detail-hero {
            background: #ffffff;
            border: 1px solid var(--tp-card-border);
            border-radius: var(--tp-radius-lg);
            padding: 1.1rem 1.25rem;
            margin: 0.5rem 0 0.85rem 0;
            box-shadow: var(--tp-shadow);
        }
        .pkg-detail-hero__title {
            margin: 0 0 0.25rem 0;
            font-size: 1.35rem;
            color: var(--tp-ink-950);
        }
        .pkg-detail-hero__tagline {
            margin: 0 0 0.65rem 0;
            color: var(--tp-ink-700);
            font-size: 0.92rem;
        }
        .pkg-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
        }
        .pkg-badge {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            background: var(--tp-lavender-100);
            color: var(--tp-purple-700);
            border: 1px solid rgba(199, 210, 254, 0.9);
        }
        .pkg-badge--duration {
            background: linear-gradient(135deg, #4a478a, #6d28d9);
            color: #ffffff;
            border: none;
        }
        .pkg-badge--city {
            background: #fafbff;
        }
        .pkg-section-cards {
            margin-top: 0.75rem;
        }
        .pkg-section-cards > .pkg-section-card:first-child {
            grid-column: 1 / -1;
        }
        .pkg-summary-bar--sync {
            visibility: hidden;
            pointer-events: none;
            user-select: none;
        }
        .pkg-section-card .pkg-highlights {
            margin: 0;
        }
        .pkg-section-card .pkg-info-block p:last-child {
            margin-bottom: 0;
        }
        .pkg-detail-main-html .pkg-detail-section__title {
            margin-top: 1rem;
        }
        .pkg-detail-section__title {
            margin: 0 0 0.45rem 0;
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--tp-purple-700);
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .pkg-highlights {
            margin: 0 0 0.85rem 0;
            padding-left: 1.1rem;
            color: #334155;
            font-size: 0.88rem;
            line-height: 1.45;
        }
        .pkg-summary-bar {
            margin: 0 0 0.65rem 0;
            padding: 0.45rem 0.75rem;
            font-size: 0.82rem;
            font-weight: 700;
            color: #ffffff;
            background: linear-gradient(90deg, #2563eb, #3b82f6);
            border-radius: 10px;
        }
        .pkg-day-breakdown {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
        }
        @media (max-width: 720px) {
            .pkg-day-breakdown { grid-template-columns: 1fr; }
        }
        .pkg-day-card {
            background: #ffffff;
            border: 1px solid #dbeafe;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
        }
        .pkg-day-card__banner {
            padding: 0.5rem 0.75rem;
            font-size: 0.82rem;
            font-weight: 700;
            color: #ffffff;
            background: linear-gradient(90deg, #1d4ed8, #3b82f6);
        }
        .pkg-day-card__body {
            padding: 0.65rem 0.75rem 0.75rem 0.75rem;
        }
        .pkg-day-card__summary {
            margin: 0 0 0.5rem 0;
            font-size: 0.8rem;
            color: var(--tp-ink-700);
        }
        .pkg-day-card__item {
            display: flex;
            gap: 0.55rem;
            align-items: flex-start;
            margin-bottom: 0.45rem;
        }
        .pkg-day-card__ico {
            flex-shrink: 0;
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 8px;
            background: #eff6ff center/70% no-repeat;
        }
        .pkg-day-card__ico--stay {
            background-color: #eff6ff;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%232563eb'%3E%3Cpath d='M4 10V20h16V10l-8-6-8 6zm2 2h12v6H6v-6z'/%3E%3C/svg%3E");
        }
        .pkg-day-card__ico--sight {
            background-color: #f0fdf4;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23059669'%3E%3Cpath d='M12 4C7 10 4 12 4 17a8 8 0 0016 0c0-5-3-7-8-13z'/%3E%3C/svg%3E");
        }
        .pkg-day-card__ico--meal {
            background-color: #fff7ed;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23ea580c'%3E%3Cpath d='M8 3v9H6V3h2zm4 0v9h-2V3h2zm4 3h2v12h-2V6z'/%3E%3C/svg%3E");
        }
        .pkg-day-card__item-label {
            margin: 0;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--tp-ink-500);
            letter-spacing: 0.03em;
        }
        .pkg-day-card__item-value {
            margin: 0.1rem 0 0 0;
            font-size: 0.84rem;
            color: #334155;
            line-height: 1.35;
        }
        .pkg-day-card__list {
            margin: 0.1rem 0 0 0;
            padding-left: 1rem;
            font-size: 0.84rem;
            color: #334155;
        }
        .pkg-info-block {
            font-size: 0.86rem;
            color: #334155;
            line-height: 1.5;
        }
        .pkg-info-block p { margin: 0 0 0.65rem 0; }
        .pkg-price-card {
            background: #ffffff;
            border: 1px solid var(--tp-card-border);
            border-radius: var(--tp-radius-lg);
            padding: 1rem 1.1rem;
            box-shadow: var(--tp-shadow);
            position: sticky;
            top: 0.5rem;
        }
        .pkg-price-card__tour {
            margin: 0;
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--tp-ink-700);
        }
        .pkg-price-card__fare-tier {
            margin: 0.15rem 0 0.55rem 0;
            font-size: 0.82rem;
            color: var(--tp-ink-500);
        }
        .pkg-price-card__was {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.45rem;
            margin-bottom: 0.35rem;
        }
        .pkg-price-card__amount {
            margin: 0;
            font-size: 1.85rem;
            font-weight: 800;
            color: #1d4ed8;
            line-height: 1.15;
        }
        .pkg-price-card__basis {
            margin: 0.2rem 0 0 0;
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--tp-ink-700);
        }
        .pkg-price-card__occ {
            margin: 0.15rem 0 0.5rem 0;
            font-size: 0.76rem;
            color: var(--tp-ink-500);
        }
        .pkg-price-card__strike {
            font-size: 0.9rem;
            color: var(--tp-ink-500);
            text-decoration: line-through;
        }
        .pkg-price-card__tag {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.22rem 0.55rem;
            border-radius: 8px;
            background: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
            margin-bottom: 0.45rem;
        }
        .pkg-price-card__total,
        .pkg-price-card__note {
            margin: 0.35rem 0 0 0;
            font-size: 0.8rem;
            color: var(--tp-ink-700);
            line-height: 1.45;
        }

        /* Nearby swap cards — white 3D tiles (override global blue label color) */
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button {
            color: #1e293b !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            border-bottom-color: #94a3b8 !important;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button p {
            color: #1e293b !important;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button p + p {
            color: #64748b !important;
            font-weight: 500 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
