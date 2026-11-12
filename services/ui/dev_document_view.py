"""
Developer docs (/dev) — root `Architecture.md` flows + `docs/ARCHITECTURE.md`.
"""

from __future__ import annotations

import html
import streamlit as st

from config import PROJECT_ROOT

APPLICATION_FLOWS_MD_PATH = PROJECT_ROOT / "Architecture.md"
DEV_FLOWS_DIR = PROJECT_ROOT / "docs" / "assets" / "dev-flows"
FLOW_PREVIEW_MAX_HEIGHT_PX = 420


def _inject_dev_flow_image_styles() -> None:
    st.markdown(
        f"""
        <style>
        [data-testid="stMain"] .block-container [data-testid="stImage"] {{
            margin: 1rem 0 1.25rem 0;
            padding: 0.35rem;
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
        }}
        [data-testid="stMain"] .block-container [data-testid="stImage"] img {{
            max-height: {FLOW_PREVIEW_MAX_HEIGHT_PX}px;
            object-fit: contain;
            width: 100%;
            display: block;
            margin: 0 auto;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def _render_application_flows_md() -> None:
    from services.ui.info_markdown_view import (
        _body_text_without_title,
        _split_markdown_and_mermaid,
        render_markdown_from_path,
    )

    if not APPLICATION_FLOWS_MD_PATH.is_file():
        st.error("`Architecture.md` was not found at the project root.")
        return

    raw = APPLICATION_FLOWS_MD_PATH.read_text(encoding="utf-8")
    title_line = "Application flows"
    for line in raw.splitlines():
        if line.startswith("# "):
            title_line = line[2:].strip()
            break

    st.markdown(
        f"""
        <div class="info-doc-wrap">
          <div class="info-doc-hero">
            <h1>{html.escape(title_line)}</h1>
            <p>On each flowchart, click the <strong>expand</strong> icon (top-right on the
            image) for full-screen view.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_markdown_from_path(
        APPLICATION_FLOWS_MD_PATH,
        apply_polish=False,
        mermaid_key_prefix="dev_flows",
        strip_leading_h1=True,
        streamlit_image_expand=True,
    )

    body_text = _body_text_without_title(raw)
    chart_idx = sum(
        1 for kind, _ in _split_markdown_and_mermaid(body_text) if kind == "mermaid"
    )
    st.caption(
        f"Rendered from `{APPLICATION_FLOWS_MD_PATH.name}` ({chart_idx} flowcharts). "
        f"PNG assets: `{DEV_FLOWS_DIR}`."
    )


def _render_architecture_md() -> None:
    from services.ui.info_markdown_view import (
        ARCHITECTURE_MD_PATH,
        _body_text_without_title,
        render_markdown_from_path,
    )

    if not ARCHITECTURE_MD_PATH.is_file():
        st.error("`docs/ARCHITECTURE.md` was not found.")
        return

    raw = ARCHITECTURE_MD_PATH.read_text(encoding="utf-8")
    title_line = (
        raw.split("\n", 1)[0].lstrip("#").strip() if raw else "Architecture"
    )

    st.markdown(
        f"""
        <div class="info-doc-wrap">
          <div class="info-doc-hero">
            <h1>{html.escape(title_line)}</h1>
            <p>Embedded flow PNGs use Streamlit&rsquo;s <strong>expand</strong> control
            (top-right on each diagram) for full-screen view.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ok = render_markdown_from_path(
        ARCHITECTURE_MD_PATH,
        apply_polish=False,
        mermaid_key_prefix="arch",
        strip_leading_h1=True,
        streamlit_image_expand=True,
    )
    if ok:
        st.caption(f"Rendered from `{ARCHITECTURE_MD_PATH.relative_to(PROJECT_ROOT)}`.")


def render_dev_document_page() -> None:
    """Render Architecture.md (flows) + docs/ARCHITECTURE.md; PNGs with Streamlit expand."""
    from services.ui.info_markdown_view import _inject_docs_styles

    _render_sidebar_nav()
    _inject_docs_styles()
    _inject_dev_flow_image_styles()

    tab_flows, tab_arch = st.tabs(["Application flows", "Architecture"])
    with tab_flows:
        _render_application_flows_md()
    with tab_arch:
        _render_architecture_md()
