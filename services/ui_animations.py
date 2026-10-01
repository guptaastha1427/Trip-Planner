"""
Trip Planner global styles — background, typography, cards (Streamlit-safe).
"""

import streamlit as st

_BG_URL = "app/static/hero-travel-bg.jpg"


def inject_page_background() -> None:
    st.markdown(
        f"""
        <div class="trip-planner-page-bg" aria-hidden="true">
            <div class="trip-planner-page-bg__image"></div>
            <div class="trip-planner-page-bg__veil"></div>
        </div>
        <style>
        .stApp,
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
            filter: blur(12px) saturate(1.05);
        }}
        .trip-planner-page-bg__veil {{
            position: absolute;
            inset: 0;
            background: rgba(255, 255, 255, 0.72);
        }}
        [data-testid="stAppViewContainer"] {{ position: relative; z-index: 1; }}
        [data-testid="stHeader"] {{
            background: rgba(255,255,255,0.65) !important;
            backdrop-filter: blur(8px);
        }}
        section[data-testid="stSidebar"] {{
            background: rgba(248,250,252,0.9) !important;
            backdrop-filter: blur(10px);
        }}
        section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"],
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
            overflow-y: auto !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
            max-height: min(420px, 55vh);
            overflow-x: hidden;
            -webkit-overflow-scrolling: touch;
            padding-right: 0.15rem;
        }}
        section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] .stButton button {{
            font-family: "Plus Jakarta Sans", system-ui, sans-serif !important;
            font-size: 0.8125rem !important;
            font-weight: 500 !important;
            color: #334155 !important;
            text-align: left !important;
            white-space: normal !important;
            line-height: 1.35 !important;
            min-height: 2.5rem;
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
            --tp-ink-950: #0c1222;
            --tp-ink-900: #0f172a;
            --tp-ink-700: #334155;
            --tp-ink-600: #475569;
            --tp-ink-500: #64748b;
            --tp-ink-400: #94a3b8;
            --tp-brand-700: #0f766e;
            --tp-brand-600: #0d9488;
            --tp-brand-500: #14b8a6;
            --tp-accent-600: #2563eb;
            --tp-accent-500: #3b82f6;
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

        section.main .block-container {
            max-width: 920px;
            padding-top: 1.25rem;
            padding-bottom: 2rem;
            color: var(--tp-ink-700);
            font-size: var(--tp-text-base);
            line-height: var(--tp-leading);
        }

        /* Page title & tagline */
        section.main h1 {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-3xl) !important;
            font-weight: 700 !important;
            color: var(--tp-ink-950) !important;
            letter-spacing: -0.03em;
            line-height: 1.15 !important;
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
            background: #fff;
            border: 1px solid #e2e8f0;
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
            background: rgba(255,255,255,0.98) !important;
            border-radius: 14px !important;
            border-color: #e2e8f0 !important;
            padding: 0.35rem 0.5rem;
            box-shadow: 0 4px 20px rgba(15,23,42,0.04);
        }
        [data-testid="stVerticalBlockBorderWrapper"]
            [data-testid="stVerticalBlockBorderWrapper"] {
            background: #f8fafc !important;
            border-color: #e8edf3 !important;
            box-shadow: none;
            margin-top: 0.35rem;
        }

        /* Tabs */
        [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        [data-baseweb="tab"] {
            font-family: var(--tp-font) !important;
            font-weight: 600 !important;
            font-size: var(--tp-text-sm) !important;
            color: var(--tp-ink-500) !important;
        }
        [data-baseweb="tab"][aria-selected="true"] {
            color: var(--tp-brand-700) !important;
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
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
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
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e2e8f0;
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
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e2e8f0;
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
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid #e2e8f0;
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
        section.main [class*="st-key-swap_"] button[kind="secondary"] {
            min-width: 268px !important;
            max-width: 268px !important;
            min-height: 4.75rem !important;
            height: auto !important;
            padding: 0.55rem 0.65rem !important;
            text-align: left !important;
            line-height: 1.35 !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #0f172a !important;
            background: #fff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06) !important;
            white-space: pre-line !important;
            word-break: break-word !important;
        }
        section.main [class*="st-key-swap_"] button[kind="secondary"]:hover {
            border-color: #3b82f6 !important;
            background: #f8fafc !important;
        }
        section.main [class*="st-key-swap_"] button[kind="secondary"] p {
            font-size: 0.72rem !important;
            font-weight: 500 !important;
            color: #64748b !important;
            margin-top: 0.25rem !important;
            line-height: 1.3 !important;
        }

        /* Buttons */
        .stButton button {
            font-family: var(--tp-font) !important;
        }
        .stButton button[kind="primary"] {
            border-radius: 10px;
            font-weight: 600 !important;
            font-size: var(--tp-text-base) !important;
            letter-spacing: 0.01em;
            background: linear-gradient(135deg, var(--tp-brand-600), var(--tp-accent-500)) !important;
            border: none !important;
        }
        .stButton button[kind="secondary"] {
            border-radius: 10px;
            font-size: var(--tp-text-sm) !important;
            font-weight: 600 !important;
            color: var(--tp-ink-700) !important;
        }

        /* Plan form inputs — white fields; beats theme secondaryBackgroundColor (#EEF2F6) */
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
            color: #0f172a !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
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
            border-color: #93c5fd !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
            outline: none !important;
        }
        section.main [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
        section.main .block-container [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div,
        section.main [data-baseweb="select"]:focus-within > div,
        section.main .block-container [data-baseweb="select"]:focus-within > div {
            background-color: #ffffff !important;
            border-color: #93c5fd !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
        }
        section.main [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"],
        section.main [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"],
        section.main .block-container [data-testid="stNumberInput"] [data-testid="stNumberInputStepUp"],
        section.main .block-container [data-testid="stNumberInput"] [data-testid="stNumberInputStepDown"] {
            background-color: #ffffff !important;
            border-color: #e2e8f0 !important;
            color: #334155 !important;
        }
        section.main [data-testid="stSelectbox"] svg,
        section.main .block-container [data-testid="stSelectbox"] svg {
            fill: #334155 !important;
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

        /* Sidebar */
        section[data-testid="stSidebar"] {
            font-size: var(--tp-text-sm);
            color: var(--tp-ink-600);
        }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p strong {
            font-family: var(--tp-font) !important;
            font-size: var(--tp-text-md) !important;
            font-weight: 700 !important;
            color: var(--tp-ink-900) !important;
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
