"""
Render info.md as a styled docs page inside Streamlit (e.g. /dev route).
"""

from __future__ import annotations

import html
import json
from typing import List, Tuple

import streamlit as st
import streamlit.components.v1 as components

from config import PROJECT_ROOT

INFO_MD_PATH = PROJECT_ROOT / "info.md"


def _split_markdown_and_mermaid(text: str) -> List[Tuple[str, str]]:
    """Return [('md', chunk), ('mermaid', diagram), ...]."""
    segments: List[Tuple[str, str]] = []
    pos = 0
    marker = "```mermaid"
    while pos < len(text):
        start = text.find(marker, pos)
        if start == -1:
            tail = text[pos:]
            if tail.strip():
                segments.append(("md", tail))
            break
        if start > pos:
            segments.append(("md", text[pos:start]))
        body_start = start + len(marker)
        if body_start < len(text) and text[body_start] == "\n":
            body_start += 1
        close = text.find("```", body_start)
        if close == -1:
            segments.append(("md", text[start:]))
            break
        diagram = text[body_start:close].strip()
        if diagram:
            segments.append(("mermaid", diagram))
        pos = close + 3
    return segments


def _inject_docs_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section.main .block-container {
            background: #f8fafc !important;
        }
        section[data-testid="stSidebar"] {
            background: #f8fafc !important;
        }
        section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            max-height: none !important;
            overflow-y: visible !important;
        }
        .trip-planner-page-bg {
            display: none !important;
        }
        [data-testid="stMain"] .block-container {
            max-width: 920px;
            padding-top: 1.25rem;
            padding-bottom: 3rem;
        }
        .info-doc-wrap {
            max-width: 920px;
            margin: 0 auto 1.5rem auto;
            padding: 0 0.5rem;
        }
        .info-doc-hero {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #0ea5e9 120%);
            color: #f8fafc;
            border-radius: 16px;
            padding: 1.75rem 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 12px 40px rgba(15, 23, 42, 0.18);
        }
        .info-doc-hero h1 {
            font-size: 1.65rem !important;
            font-weight: 700 !important;
            margin: 0 0 0.5rem 0 !important;
            color: #fff !important;
            border: none !important;
        }
        .info-doc-hero p {
            margin: 0;
            opacity: 0.92;
            font-size: 0.95rem;
            line-height: 1.5;
        }
        [data-testid="stMain"] .block-container h2,
        .info-doc-body h2 {
            margin-top: 2rem;
            padding-bottom: 0.35rem;
            border-bottom: 2px solid #e2e8f0;
            color: #0f172a;
        }
        [data-testid="stMain"] .block-container h3,
        .info-doc-body h3 { color: #1e293b; margin-top: 1.25rem; }
        [data-testid="stMain"] .block-container blockquote,
        .info-doc-body blockquote {
            border-left: 4px solid #0ea5e9;
            background: #f0f9ff;
            padding: 0.75rem 1rem;
            border-radius: 0 8px 8px 0;
            margin: 1rem 0;
        }
        [data-testid="stMain"] .block-container table,
        .info-doc-body table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            margin: 1rem 0;
        }
        [data-testid="stMain"] .block-container th,
        .info-doc-body th {
            background: #f1f5f9;
            text-align: left;
            padding: 0.5rem 0.65rem;
            border: 1px solid #e2e8f0;
        }
        [data-testid="stMain"] .block-container td,
        .info-doc-body td {
            padding: 0.5rem 0.65rem;
            border: 1px solid #e2e8f0;
            vertical-align: top;
        }
        [data-testid="stMain"] .block-container code,
        .info-doc-body code {
            background: #f1f5f9;
            padding: 0.12rem 0.35rem;
            border-radius: 4px;
            font-size: 0.85em;
        }
        [data-testid="stMain"] .block-container pre,
        .info-doc-body pre {
            background: #0f172a !important;
            border-radius: 10px;
            padding: 1rem !important;
        }
        .info-mermaid-card {
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 0.5rem;
            margin: 1.25rem 0;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _mermaid_iframe_height(diagram: str) -> int:
    lines = diagram.count("\n") + 1
    extra = diagram.count("subgraph") * 36 + diagram.count("flowchart TD") * 20
    return min(920, max(240, 110 + lines * 30 + extra))


def _render_mermaid(diagram: str, key: str) -> None:
    diagram_js = json.dumps(diagram)
    element_id = f"mm_{key}"
    height = _mermaid_iframe_height(diagram)
    components.html(
        f"""
        <div class="info-mermaid-card">
          <pre class="mermaid" id="{element_id}"></pre>
        </div>
        <script>
          (function () {{
            var el = document.getElementById({json.dumps(element_id)});
            el.textContent = {diagram_js};
            function render() {{
              mermaid.initialize({{
                startOnLoad: false,
                theme: "neutral",
                securityLevel: "loose",
                flowchart: {{ htmlLabels: true, curve: "basis" }}
              }});
              mermaid.run({{ nodes: [el] }}).catch(function (err) {{
                el.textContent = String(err);
              }});
            }}
            if (window.mermaid) {{
              render();
              return;
            }}
            var s = document.createElement("script");
            s.src = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js";
            s.onload = render;
            s.onerror = function () {{
              el.textContent = "Could not load Mermaid (check network).";
            }};
            document.head.appendChild(s);
          }})();
        </script>
        """,
        height=height,
        scrolling=True,
    )


def _body_text_without_title(raw: str) -> str:
    """Drop the leading # title so the hero is not duplicated in the body."""
    if not raw.startswith("#"):
        return raw
    nl = raw.find("\n")
    return raw[nl + 1 :].lstrip() if nl != -1 else ""


def _render_sidebar_nav() -> None:
    st.sidebar.header("Navigation")
    try:
        import app as trip_app

        st.sidebar.page_link(
            trip_app.TRIP_PLANNER_PAGE,
            label="Back to Trip Planner",
            icon="🏠",
        )
    except Exception:
        st.sidebar.link_button("Back to Trip Planner", "/", use_container_width=True)


def render_info_document_page() -> None:
    """Full-page reader for info.md."""
    _render_sidebar_nav()
    _inject_docs_styles()

    if not INFO_MD_PATH.is_file():
        st.error("`info.md` was not found in the project root.")
        return

    raw = INFO_MD_PATH.read_text(encoding="utf-8")
    title_line = raw.split("\n", 1)[0].lstrip("#").strip() if raw else "Project guide"
    body_text = _body_text_without_title(raw)

    st.markdown(
        f"""
        <div class="info-doc-wrap">
          <div class="info-doc-hero">
            <h1>{html.escape(title_line)}</h1>
            <p>Architecture, flows, and how this app works — rendered from <code>info.md</code>.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    segments = _split_markdown_and_mermaid(body_text)
    mermaid_idx = 0
    for kind, chunk in segments:
        if kind == "md":
            st.markdown(chunk, unsafe_allow_html=False)
        else:
            _render_mermaid(chunk, key=f"mermaid_{mermaid_idx}")
            mermaid_idx += 1

    st.caption("Tip: Edit `info.md` in the repo and refresh this page to see updates.")
