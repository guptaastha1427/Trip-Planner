"""
Trip Planner global styles — background, typography, cards (Streamlit-safe).
"""

import streamlit as st

from services.ui_travel_theme import inject_travel_light_theme

_BG_URL = "app/static/hero-travel-bg.jpg"


def inject_page_background() -> None:
    st.markdown(
        f"""
        <div class="trip-planner-page-bg" aria-hidden="true">
            <div class="trip-planner-page-bg__image"></div>
            <div class="trip-planner-page-bg__veil"></div>
        </div>
        <style>
        .stApp {{
            background: linear-gradient(160deg, #eef2ff 0%, #f5f3ff 45%, #ede9fe 100%) !important;
            min-height: 100vh;
        }}
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section.main,
        section.main .block-container {{
            background: transparent !important;
        }}
        .trip-planner-page-bg {{
            position: fixed;
            inset: 0;
            z-index: 0;
            pointer-events: none;
            overflow: hidden;
        }}
        .trip-planner-page-bg__image {{
            position: absolute;
            inset: -20px;
            background: url("{_BG_URL}") center/cover no-repeat;
            filter: blur(22px) saturate(1.1) brightness(1.05);
            opacity: 0.22;
        }}
        .trip-planner-page-bg__veil {{
            position: absolute;
            inset: 0;
            background:
                radial-gradient(ellipse 75% 55% at 12% 8%, rgba(167, 139, 250, 0.28), transparent 58%),
                radial-gradient(ellipse 65% 50% at 88% 92%, rgba(129, 140, 248, 0.22), transparent 52%),
                linear-gradient(160deg, #eef2ff 0%, #f8fafc 50%, #f5f3ff 100%);
        }}
        [data-testid="stAppViewContainer"] {{ position: relative; z-index: 1; }}
        [data-testid="stHeader"] {{
            background: rgba(255, 255, 255, 0.72) !important;
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        }}
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.88) !important;
            backdrop-filter: blur(14px);
            border-right: 1px solid rgba(199, 210, 254, 0.55);
        }}
        /* Expanded: transform anchors fixed profile dock to the sidebar panel */
        section[data-testid="stSidebar"][aria-expanded="true"] {{
            position: relative !important;
            transform: translateZ(0) !important;
            overflow: visible !important;
        }}
        /* Collapsed: clip content so labels do not wrap in a narrow strip */
        section[data-testid="stSidebar"][aria-expanded="false"] {{
            overflow: hidden !important;
            min-width: 0 !important;
            border-right: none !important;
        }}
        section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarUserContent"],
        section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarNav"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button {{
            width: 2rem !important;
            height: 2rem !important;
            min-width: 2rem !important;
            min-height: 2rem !important;
            padding: 0 !important;
            border-radius: 10px !important;
            border: 1px solid transparent !important;
            background: transparent !important;
            color: #64748b !important;
            transition:
                background 0.15s ease,
                border-color 0.15s ease,
                color 0.15s ease,
                box-shadow 0.15s ease,
                transform 0.12s ease !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover,
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:hover button {{
            background: rgba(124, 108, 240, 0.12) !important;
            border-color: rgba(124, 108, 240, 0.28) !important;
            color: #4a478a !important;
            box-shadow: 0 2px 8px rgba(74, 71, 138, 0.12) !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:active,
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"]:active button {{
            background: rgba(124, 108, 240, 0.2) !important;
            transform: scale(0.94) !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button:focus-visible {{
            outline: 2px solid rgba(124, 108, 240, 0.55) !important;
            outline-offset: 2px !important;
        }}
        [data-testid="stSidebarNavViewButton"] button {{
            border-radius: 10px !important;
            transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease !important;
        }}
        [data-testid="stSidebarNavViewButton"] button:hover {{
            background: rgba(124, 108, 240, 0.12) !important;
            color: #4a478a !important;
            box-shadow: 0 2px 8px rgba(74, 71, 138, 0.12) !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {{
            max-height: 100vh !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            -webkit-overflow-scrolling: touch;
            padding-bottom: 0 !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{
            padding-bottom: 6.5rem !important;
        }}
        section[data-testid="stSidebar"] [class*="st-key-trip_history_scroll"],
        section[data-testid="stSidebar"] [class*="st-key-trip_history_scroll"] [data-testid="stVerticalBlock"] {{
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch;
        }}
        section[data-testid="stSidebar"] [class*="st-key-trip_history_scroll"] .stButton button {{
            font-family: "Plus Jakarta Sans", system-ui, sans-serif !important;
            font-size: 0.8125rem !important;
            font-weight: 600 !important;
            text-align: left !important;
            white-space: normal !important;
            line-height: 1.35 !important;
            min-height: 2.5rem;
        }}
        section[data-testid="stSidebar"] [class*="st-key-trip_history_scroll"] .stButton button p {{
            color: #ffffff !important;
            text-align: left !important;
        }}
        section[data-testid="stSidebar"] nav a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"] {{
            white-space: normal !important;
            line-height: 1.45 !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {{
            padding-bottom: 0.5rem !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul {{
            margin-bottom: 0.65rem !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[href*="document-assistant"],
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"][href*="document-assistant"] {{
            display: none !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] li:has(a[href*="document-assistant"]) {{
            display: none !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_ui_animations() -> None:
    inject_page_background()
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

        :root {
            --tp-font: "Plus Jakarta Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
            --tp-ink-950: #1e1b4b;
            --tp-ink-900: #312e81;
            --tp-ink-700: #475569;
            --tp-ink-600: #64748b;
            --tp-ink-500: #64748b;
            --tp-ink-400: #94a3b8;
            --tp-brand-700: #4a478a;
            --tp-brand-600: #5b57a6;
            --tp-brand-500: #7c6cf0;
            --tp-accent-600: #6d28d9;
            --tp-accent-500: #8b5cf6;
            --tp-warm-600: #c2410c;
            --tp-map-600: #059669;
            --tp-text-xs: 0.75rem;
            --tp-text-sm: 0.8125rem;
            --tp-text-base: 0.9375rem;
            --tp-text-md: 1rem;
            --tp-text-lg: 1.125rem;
            --tp-text-xl: 1.375rem;
            --tp-text-2xl: 1.75rem;
            --tp-text-3xl: 2rem;
            --tp-leading: 1.55;
            --tp-leading-tight: 1.35;
        }

        html, body, .stApp, [data-testid="stAppViewContainer"],
        section.main, section[data-testid="stSidebar"] {
            font-family: var(--tp-font) !important;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        [data-testid="stMainBlockContainer"].block-container,
        section.main .block-container {
            --tp-main-gutter: 1.25rem;
            max-width: 1100px;
            padding-top: var(--tp-main-gutter) !important;
            padding-left: var(--tp-main-gutter) !important;
            padding-right: var(--tp-main-gutter) !important;
            padding-bottom: 1.5rem !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: 0 !important;
            box-sizing: border-box !important;
            color: var(--tp-ink-700);
            font-size: var(--tp-text-base);
            line-height: var(--tp-leading);
            transition: opacity 0.3s ease-in-out;
        }
        section.main [data-testid="stVerticalBlock"]:first-of-type {
            gap: 0.5rem;
        }

        /* Page title & tagline */
        section.main h1 {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-3xl) !important;
            font-weight: 700 !important;
            color: var(--tp-ink-950) !important;
            letter-spacing: -0.03em;
            line-height: 1.15 !important;
            margin-top: 0 !important;
            margin-bottom: 0.2rem !important;
        }
        section.main [data-testid="stCaptionContainer"],
        section.main .stCaption, section.main p[data-testid="stCaption"] {
            color: var(--tp-ink-500) !important;
            font-size: var(--tp-text-sm) !important;
            font-weight: 500 !important;
            line-height: var(--tp-leading) !important;
        }
        section.main h2, section.main h3, section.main h4 {
            font-family: var(--tp-font) !important;
            color: var(--tp-ink-900) !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }
        section.main h4 {
            font-size: var(--tp-text-lg) !important;
            margin-top: 0.5rem !important;
        }

        /* Section labels */
        .trip-h {
            font-family: var(--tp-font);
            font-size: var(--tp-text-xl);
            font-weight: 700;
            margin: 1.1rem 0 0.55rem;
            color: var(--tp-ink-900);
            letter-spacing: -0.02em;
            line-height: var(--tp-leading-tight);
        }
        .trip-h--plan { color: var(--tp-accent-600); }
        .trip-h--itinerary { color: var(--tp-warm-600); }
        .trip-h--map { color: var(--tp-map-600); }
        .trip-h--travel { color: var(--tp-brand-700); }
        .trip-h--travel-sub {
            font-size: var(--tp-text-md);
            font-weight: 600;
            color: var(--tp-ink-500);
            margin-top: 0.85rem;
            letter-spacing: -0.01em;
        }
        .trip-h--day {
            font-size: var(--tp-text-lg);
            font-weight: 700;
            color: #6d28d9;
            margin-top: 1.25rem;
            margin-bottom: 0.35rem;
            padding-bottom: 0.3rem;
            border-bottom: 2px solid rgba(109, 40, 217, 0.18);
        }

        /* Stats row */
        .trip-stats {
            display: flex;
            gap: 0.65rem;
            margin: 0.75rem 0 1rem;
            flex-wrap: wrap;
        }
        .trip-stats__cell {
            flex: 1;
            min-width: 100px;
            text-align: center;
            padding: 0.75rem 0.5rem;
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid rgba(199, 210, 254, 0.65);
        }
        .trip-stats__cell strong {
            display: block;
            font-size: var(--tp-text-lg);
            font-weight: 700;
            color: var(--tp-ink-950);
            letter-spacing: -0.02em;
        }
        .trip-stats__cell span {
            font-size: var(--tp-text-xs);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--tp-ink-400);
            font-weight: 600;
        }

        /* Bordered Streamlit containers */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.98) !important;
            border-radius: 22px !important;
            border-color: rgba(199, 210, 254, 0.65) !important;
            padding: 0.35rem 0.5rem;
            box-shadow: 0 14px 40px rgba(74, 71, 138, 0.1);
        }
        [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stVerticalBlockBorderWrapper"] {
            background: #fafbff !important;
            border-color: #e8eeff !important;
            box-shadow: none;
            margin-top: 0.35rem;
        }

        /* Tabs — hide Base Web underline / sliding indicator bars */
        [data-baseweb="tab-border"],
        [data-baseweb="tab-highlight"] {
            display: none !important;
            height: 0 !important;
            border: none !important;
            background: transparent !important;
        }
        /* Hint cards — horizontal scroll */
        .hint-scroll {
            display: flex;
            align-items: stretch;
            gap: 0.75rem;
            overflow-x: auto;
            padding: 0.25rem 0 0.75rem;
            scroll-snap-type: x mandatory;
        }
        .hint-card {
            flex: 0 0 208px;
            scroll-snap-align: start;
            display: flex;
            flex-direction: column;
            background: #ffffff;
            border: 1px solid rgba(199, 210, 254, 0.65);
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 28px rgba(0, 0, 0, 0.32);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .hint-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(15,23,42,0.08);
        }
        .hint-card__media {
            flex: 0 0 100px;
            height: 100px;
            min-height: 100px;
            overflow: hidden;
            background: linear-gradient(145deg, #e8eef5 0%, #f1f5f9 48%, #e2e8f0 100%);
        }
        .hint-card__img {
            width: 100%;
            height: 100%;
            min-height: 100px;
            object-fit: cover;
            object-position: center;
            display: block;
        }
        .hint-card__placeholder {
            width: 100%;
            height: 100%;
            min-height: 100px;
            background: linear-gradient(145deg, #dbe4f0 0%, #f8fafc 55%, #e2e8f0 100%);
        }
        .hint-card__body {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 0.5rem 0.55rem 0.55rem;
            min-height: 7.5rem;
        }
        .hint-card__title {
            font-family: var(--tp-font);
            font-size: var(--tp-text-sm);
            font-weight: 700;
            margin: 0 0 0.2rem;
            color: var(--tp-ink-900);
            line-height: 1.3;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .hint-card__sub {
            font-size: var(--tp-text-xs);
            font-weight: 500;
            color: var(--tp-ink-500);
            margin: 0;
            line-height: 1.35;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            flex: 1;
        }
        .hint-card__meta {
            font-size: 0.7rem;
            font-weight: 500;
            color: var(--tp-ink-400);
            margin: 0.35rem 0 0;
            line-height: 1.35;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
        .hint-card__links {
            margin: 0.4rem 0 0;
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem 0.65rem;
        }
        .hint-card__link {
            font-size: var(--tp-text-xs);
            font-weight: 600;
            color: var(--tp-accent-600);
            text-decoration: none;
        }
        .hint-card__link:hover {
            text-decoration: underline;
            color: #1d4ed8;
        }

        .stop-card__placeholder {
            width: 100%;
            min-height: 120px;
            border-radius: 10px;
            background: linear-gradient(145deg, #dbe4f0 0%, #f8fafc 55%, #e2e8f0 100%);
        }
        .dest-guide-card {
            background: #ffffff;
            border: 1px solid rgba(199, 210, 254, 0.65);
            border-radius: 12px;
            padding: 0.75rem 0.9rem;
            margin: 0.35rem 0 0.85rem;
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
        }
        .dest-guide-card__title {
            margin: 0 0 0.4rem;
            font-size: var(--tp-text-md);
            font-weight: 700;
            color: var(--tp-ink-900);
        }
        .dest-guide-card__about {
            margin: 0 0 0.65rem;
            font-size: var(--tp-text-sm);
            font-weight: 400;
            line-height: var(--tp-leading);
            color: var(--tp-ink-600);
        }
        .dest-guide-card__grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.5rem;
        }
        @media (max-width: 640px) {
            .dest-guide-card__grid { grid-template-columns: 1fr; }
        }
        .dest-guide-card__cell {
            border-radius: 10px;
            padding: 0.45rem 0.55rem;
            font-size: 0.78rem;
            line-height: 1.4;
            color: #334155;
        }
        .dest-guide-card__cell p { margin: 0.2rem 0 0; }
        .dest-guide-card__cell--good {
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
        }
        .dest-guide-card__cell--avoid {
            background: #fff7ed;
            border: 1px solid #fed7aa;
        }
        .dest-guide-card__label {
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            color: #64748b;
        }
        .dest-guide-card__tip {
            margin: 0.55rem 0 0;
            font-size: 0.74rem;
            color: #64748b;
        }
        .weather-card {
            background: #ffffff;
            border: 1px solid rgba(199, 210, 254, 0.65);
            border-radius: 12px;
            padding: 0.65rem 0.85rem;
            margin: 0.25rem 0 0.85rem;
        }
        .weather-card__summary {
            margin: 0;
            font-size: 0.8rem;
            color: #475569;
        }
        .weather-card__now {
            margin: 0.35rem 0 0.5rem;
            font-size: 0.9rem;
            color: #0f172a;
        }
        .weather-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }
        .weather-chip {
            flex: 0 0 auto;
            min-width: 4.2rem;
            text-align: center;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.35rem 0.4rem;
            font-size: 0.72rem;
            color: #475569;
        }
        .weather-chip__icon { display: block; font-size: 1.1rem; }
        .weather-chip__temp { display: block; font-weight: 600; color: #0f172a; }

        .travel-tips-card {
            background: #ffffff;
            border: 1px solid rgba(199, 210, 254, 0.65);
            border-radius: 12px;
            padding: 0.55rem 0.85rem;
            margin: 0.45rem 0 0.85rem;
            box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
        }
        .travel-tips-card__list {
            margin: 0;
            padding: 0;
            list-style: none;
        }
        .travel-tips-card__item {
            font-size: var(--tp-text-sm);
            font-weight: 400;
            color: var(--tp-ink-600);
            line-height: var(--tp-leading);
            padding: 0.32rem 0 0.32rem 0.95rem;
            position: relative;
            border-bottom: 1px solid #f1f5f9;
        }
        .travel-tips-card__item:last-child {
            border-bottom: none;
            padding-bottom: 0.15rem;
        }
        .travel-tips-card__item::before {
            content: "";
            position: absolute;
            left: 0;
            top: 0.55rem;
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #cbd5e1;
        }

        .trip-tip-list, .ui-tip-list {
            margin: 0.25rem 0 0.75rem 1rem;
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.5;
        }

        /* Nearby scroll — flex children need min-width:0 on columns/borders */
        [data-testid="stVerticalBlockBorderWrapper"] {
            overflow-x: visible !important;
        }
        [data-testid="column"] {
            min-width: 0 !important;
            overflow: visible !important;
        }
        .ui-nearby-label {
            font-size: var(--tp-text-xs);
            font-weight: 600;
            color: var(--tp-ink-500);
            letter-spacing: 0.02em;
            text-transform: uppercase;
            margin: 0.45rem 0 0.35rem;
        }
        /* Nearby swap row — horizontal container + full-name card buttons */
        section.main [class*="st-key-nearby_row_"] [data-testid="stHorizontalBlock"],
        section.main [data-testid="stHorizontalBlock"]:has([class*="st-key-swap_"]) {
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
            max-width: 100%;
            padding-bottom: 0.35rem;
            -webkit-overflow-scrolling: touch;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button {
            min-width: 268px !important;
            max-width: 268px !important;
            min-height: 4.75rem !important;
            height: auto !important;
            padding: 0.55rem 0.65rem !important;
            text-align: left !important;
            line-height: 1.35 !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #1e293b !important;
            background: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-bottom-width: 4px !important;
            border-bottom-color: #94a3b8 !important;
            border-radius: var(--tp-btn-radius, 0.5rem) !important;
            box-shadow: none !important;
            white-space: pre-line !important;
            word-break: break-word !important;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button:hover {
            filter: brightness(1.03) !important;
            transform: translateY(-1px) !important;
            border-bottom-width: 6px !important;
            background: #f8fafc !important;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button:active {
            filter: brightness(0.97) !important;
            transform: translateY(2px) !important;
            border-bottom-width: 2px !important;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button p {
            color: #1e293b !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            margin: 0 !important;
            line-height: 1.35 !important;
        }
        section.main [class*="st-key-swap_"] [data-testid="stButton"] button p + p {
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            color: #64748b !important;
            margin-top: 0.25rem !important;
            line-height: 1.3 !important;
        }

        /* Buttons — font only (3D look from inject_travel_light_theme) */
        .stButton button,
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stDownloadButton"] button,
        [data-testid="stLinkButton"] a {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-base) !important;
            letter-spacing: 0.01em;
        }

        /* Form inputs — dark glass */
        section.main input[data-testid="stTextInputField"],
        section.main .block-container input[data-testid="stTextInputField"],
        section.main textarea,
        section.main .block-container textarea,
        section.main [data-testid="stNumberInputContainer"] input,
        section.main .block-container [data-testid="stNumberInputContainer"] input,
        section.main [data-testid="stNumberInputField"],
        section.main .block-container [data-testid="stNumberInputField"],
        section.main [data-testid="stTextInput"] input,
        section.main .block-container [data-testid="stTextInput"] input,
        section.main [data-testid="stNumberInput"] input,
        section.main .block-container [data-testid="stNumberInput"] input,
        section.main [data-testid="stTextArea"] textarea,
        section.main .block-container [data-testid="stTextArea"] textarea,
        section.main [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        section.main .block-container [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        section.main [data-baseweb="select"] > div,
        section.main .block-container [data-baseweb="select"] > div,
        section.main [data-baseweb="input"] input,
        section.main .block-container [data-baseweb="input"] input,
        section.main div[data-baseweb="input"],
        section.main .block-container div[data-baseweb="input"],
        section.main [role="combobox"],
        section.main .block-container [role="combobox"] {
            background-color: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-base) !important;
            font-weight: 500 !important;
        }
        section.main input[data-testid="stTextInputField"]:focus,
        section.main .block-container input[data-testid="stTextInputField"]:focus,
        section.main textarea:focus,
        section.main .block-container textarea:focus,
        section.main [data-testid="stNumberInputContainer"] input:focus,
        section.main .block-container [data-testid="stNumberInputContainer"] input:focus,
        section.main [data-testid="stNumberInputField"]:focus,
        section.main .block-container [data-testid="stNumberInputField"]:focus,
        section.main [data-baseweb="input"] input:focus,
        section.main .block-container [data-baseweb="input"] input:focus,
        section.main [role="combobox"]:focus {
            background-color: #ffffff !important;
            color: #0f172a !important;
            border-color: rgba(74, 71, 138, 0.45) !important;
            box-shadow: 0 0 0 3px rgba(124, 108, 240, 0.18) !important;
            outline: none !important;
        }
        section.main [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
        section.main .block-container [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
        section.main [data-baseweb="select"]:focus-within > div,
        section.main .block-container [data-baseweb="select"]:focus-within > div {
            background-color: rgba(15, 23, 42, 0.92) !important;
            border-color: rgba(34, 211, 238, 0.55) !important;
            box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.22) !important;
        }
        section.main [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"],
        section.main [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"],
        section.main .block-container [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"],
        section.main .block-container [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"] {
            background-color: #f8fafc !important;
            border-color: rgba(148, 163, 184, 0.22) !important;
            color: #e2e8f0 !important;
        }
        section.main [data-testid="stSelectbox"] svg,
        section.main .block-container [data-testid="stSelectbox"] svg {
            fill: #cbd5e1 !important;
        }
        section.main [data-testid="stTextInput"] label,
        section.main [data-testid="stNumberInput"] label,
        section.main [data-testid="stSelectbox"] label,
        section.main [data-testid="stTextArea"] label,
        section.main .block-container [data-testid="stTextInput"] label,
        section.main .block-container [data-testid="stNumberInput"] label,
        section.main .block-container [data-testid="stSelectbox"] label,
        section.main .block-container [data-testid="stTextArea"] label {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-sm) !important;
            font-weight: 600 !important;
            color: var(--tp-ink-600) !important;
            letter-spacing: 0.01em;
        }

        /* Itinerary stop titles */
        section.main [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stMarkdownContainer"] p strong {
            font-size: var(--tp-text-md) !important;
            font-weight: 700 !important;
            color: var(--tp-ink-950) !important;
        }
        section.main [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stMarkdownContainer"] p {
            font-size: var(--tp-text-sm);
            color: var(--tp-ink-600);
            line-height: var(--tp-leading);
        }

        /* Body text */
        section.main [data-testid="stMarkdownContainer"] p,
        section.main [data-testid="stMarkdownContainer"] li {
            font-family: var(--tp-font);
            line-height: var(--tp-leading);
            color: var(--tp-ink-700);
            font-size: var(--tp-text-base);
        }
        section.main [data-testid="stMarkdownContainer"] a {
            color: var(--tp-brand-700);
            font-weight: 600;
        }

        /* Alerts & expanders */
        [data-testid="stAlert"] {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-sm) !important;
            line-height: var(--tp-leading) !important;
        }
        [data-testid="stExpander"] summary {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-sm) !important;
            font-weight: 600 !important;
            color: var(--tp-ink-800, var(--tp-ink-700)) !important;
        }

        /* Sidebar — keep nav at full size; only captions use smaller text */
        section[data-testid="stSidebar"] {
            font-size: var(--tp-text-base);
            color: var(--tp-ink-600);
        }
        section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        section[data-testid="stSidebar"] .stCaption {
            font-size: var(--tp-text-sm) !important;
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p strong {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-md) !important;
            font-weight: 700 !important;
            color: var(--tp-ink-900) !important;
        }
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavLink"] {
            font-size: 1rem !important;
            font-weight: 500 !important;
        }

        hr { display: none; }

        /* Route map — tall enough to explore stops */
        [data-testid="stDeckGlJsonChart"],
        [data-testid="stPydeckChart"] {
            min-height: 420px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #e2e8f0;
        }

        /* Map hover card — always light (readable on light & dark UI theme) */
        #deckgl-tooltip,
        .deckgl-tooltip,
        div#deckgl-tooltip {
            background: #ffffff !important;
            color: #1e293b !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.18) !important;
            padding: 0 !important;
            max-width: 260px !important;
            font-family: var(--tp-font) !important;
            opacity: 1 !important;
        }
        #deckgl-tooltip *,
        .deckgl-tooltip * {
            color: inherit;
        }
        [data-testid="stDeckGlJsonChart"] #deckgl-tooltip,
        [data-testid="stPydeckChart"] #deckgl-tooltip {
            background-color: #ffffff !important;
            color: #0f172a !important;
            filter: none !important;
            color-scheme: only light !important;
        }
        .trip-map-tooltip {
            padding: 12px 14px;
            background: #ffffff;
            color: #334155;
            font-size: 13px;
            line-height: 1.45;
        }
        .trip-map-tooltip__title {
            font-size: 14px;
            font-weight: 700;
            color: #0f172a !important;
            margin-bottom: 4px;
        }
        .trip-map-tooltip__meta {
            font-size: 12px;
            font-weight: 500;
            color: #475569 !important;
        }
        .trip-map-tooltip__day {
            font-size: 12px;
            font-style: italic;
            color: #64748b !important;
            margin-top: 4px;
        }
        .trip-map-tooltip__hint {
            font-size: 12px;
            color: #334155 !important;
            margin-top: 6px;
        }
        .trip-map-tooltip__img {
            display: block;
            width: 100%;
            max-width: 220px;
            border-radius: 8px;
            margin-top: 8px;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.1);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    inject_travel_light_theme()
