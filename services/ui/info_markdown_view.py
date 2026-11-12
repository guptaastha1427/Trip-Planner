"""
Render info.md as a styled docs page inside Streamlit (e.g. /dev route).
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st
import streamlit.components.v1 as components

from config import PROJECT_ROOT
from services.ui.ui_copy import polish_ui_copy

INFO_MD_PATH = PROJECT_ROOT / "info.md"
ARCHITECTURE_MD_PATH = PROJECT_ROOT / "docs" / "ARCHITECTURE.md"

_MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_ARCH_FLOW_DIAGRAM_RE = re.compile(
    r'<div\s+class="arch-flow-diagram"[^>]*>[\s\S]*?</div>',
    re.IGNORECASE,
)
_IMAGE_PAYLOAD_SEP = "\x1f"


def _alt_path_from_img_tag(tag: str) -> Tuple[str, str]:
    src_m = re.search(r'\bsrc=["\']([^"\']+)["\']', tag, re.IGNORECASE)
    path = src_m.group(1).strip() if src_m else ""
    alt_m = re.search(r'\balt=["\']([^"\']*)["\']', tag, re.IGNORECASE)
    alt = alt_m.group(1) if alt_m else ""
    return alt, path


def _image_match_spans(text: str) -> List[Tuple[int, int, str, str]]:
    """Return sorted (start, end, alt, path) for flow blocks, markdown, and HTML images."""
    spans: List[Tuple[int, int, str, str]] = []
    for match in _ARCH_FLOW_DIAGRAM_RE.finditer(text):
        img_m = re.search(r"<img\s+[^>]*>", match.group(0), re.IGNORECASE)
        if img_m:
            alt, path = _alt_path_from_img_tag(img_m.group(0))
            if path:
                spans.append((match.start(), match.end(), alt, path))
    for match in _MARKDOWN_IMAGE_RE.finditer(text):
        spans.append(
            (match.start(), match.end(), match.group(1), match.group(2).strip())
        )
    html_img = re.compile(
        r'<img\s+[^>]*\bsrc=["\']([^"\']+)["\'][^>]*>',
        re.IGNORECASE,
    )
    for match in html_img.finditer(text):
        tag = match.group(0)
        alt, path = _alt_path_from_img_tag(tag)
        if path:
            spans.append((match.start(), match.end(), alt, path))
    spans.sort(key=lambda t: t[0])
    merged: List[Tuple[int, int, str, str]] = []
    last_end = -1
    for start, end, alt, path in spans:
        if start < last_end:
            continue
        merged.append((start, end, alt, path))
        last_end = end
    return merged


def _split_md_images(text: str) -> List[Tuple[str, str]]:
    """Split a markdown fragment into ``md`` / ``image`` segments (image payload: alt\\x1fpath)."""
    segments: List[Tuple[str, str]] = []
    spans = _image_match_spans(text)
    if not spans:
        if text:
            segments.append(("md", text))
        return segments
    pos = 0
    for start, end, alt, path in spans:
        if start > pos:
            segments.append(("md", text[pos:start]))
        segments.append(("image", f"{alt}{_IMAGE_PAYLOAD_SEP}{path}"))
        pos = end
    if pos < len(text):
        segments.append(("md", text[pos:]))
    return segments


def _parse_image_payload(payload: str) -> Tuple[str, str]:
    if _IMAGE_PAYLOAD_SEP in payload:
        alt, path = payload.split(_IMAGE_PAYLOAD_SEP, 1)
        return alt, path
    return "", payload


def _resolve_markdown_image(md_path: Path, rel_path: str) -> Optional[Path]:
    raw = (rel_path or "").strip()
    if not raw or raw.startswith(("http://", "https://", "data:")):
        return None
    candidate = (md_path.parent / raw).resolve()
    return candidate if candidate.is_file() else None


def _render_markdown_image(
    md_path: Path,
    alt: str,
    rel_path: str,
    *,
    use_streamlit_expand: bool,
) -> None:
    if use_streamlit_expand:
        resolved = _resolve_markdown_image(md_path, rel_path)
        if resolved is not None:
            caption = alt.strip() or None
            st.image(str(resolved), width="stretch", caption=caption)
            return
    st.markdown(f"![{alt}]({rel_path})", unsafe_allow_html=False)


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
            background: linear-gradient(135deg, #312e81 0%, #6366f1 55%, #818cf8 120%);
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
            border-left: 4px solid #6366f1;
            background: #eef2ff;
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
    edges = diagram.count("-->")
    decisions = diagram.count("{")
    extra = diagram.count("subgraph") * 36
    td_bonus = 24 if "flowchart TD" in diagram else 0
    return min(
        1100,
        max(260, 100 + lines * 26 + edges * 14 + decisions * 50 + extra + td_bonus),
    )


def _render_mermaid(diagram: str, key: str, *, height: Optional[int] = None) -> None:
    diagram_js = json.dumps(diagram)
    element_id = f"mm_{key}"
    frame_height = height if height is not None else _mermaid_iframe_height(diagram)
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
              mermaid.run({{ nodes: [el] }}).then(function () {{
                try {{
                  window.dispatchEvent(new Event("resize"));
                }} catch (e) {{}}
              }}).catch(function (err) {{
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
        height=frame_height,
        scrolling=True,
    )


def _strip_trailing_section_heading(md_chunk: str) -> tuple[str, Optional[str]]:
    """If the chunk ends with ``## Title``, return body without that line and the title."""
    lines = md_chunk.rstrip().split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and lines[-1].strip().startswith("## "):
        title = lines[-1].strip()[3:].strip()
        body = "\n".join(lines[:-1])
        return body, title
    return md_chunk, None


def render_markdown_from_path(
    md_path,
    *,
    mermaid_key_prefix: str = "mermaid",
    apply_polish: bool = True,
    mermaid_in_expander: bool = False,
    mermaid_expander_first_open: bool = False,
    mermaid_expander_label: str = "View flowchart",
    strip_leading_h1: bool = False,
    streamlit_image_expand: bool = False,
) -> bool:
    """Render a markdown file with interleaved ```mermaid blocks. Returns False if missing."""
    md_file = Path(md_path)
    if not md_file.is_file():
        return False
    raw = md_file.read_text(encoding="utf-8")
    if strip_leading_h1 and raw.startswith("#"):
        raw = _body_text_without_title(raw)
    segments = _split_markdown_and_mermaid(raw)
    mermaid_idx = 0
    i = 0
    while i < len(segments):
        kind, chunk = segments[i]
        if kind == "md":
            body = chunk
            expander_title: Optional[str] = None
            if (
                mermaid_in_expander
                and i + 1 < len(segments)
                and segments[i + 1][0] == "mermaid"
            ):
                body, expander_title = _strip_trailing_section_heading(chunk)
            text = polish_ui_copy(body) if apply_polish else body
            md_parts = (
                _split_md_images(text)
                if streamlit_image_expand
                else [("md", text)]
            )
            for part_kind, part in md_parts:
                if part_kind == "md":
                    if part.strip():
                        allow_html = streamlit_image_expand and (
                            "<div" in part or "<style" in part
                        )
                        st.markdown(part, unsafe_allow_html=allow_html)
                else:
                    alt, rel = _parse_image_payload(part)
                    _render_markdown_image(
                        md_file,
                        alt,
                        rel,
                        use_streamlit_expand=streamlit_image_expand,
                    )
            if expander_title is not None:
                st.markdown(f"## {expander_title}")
                expanded = mermaid_expander_first_open and mermaid_idx == 0
                with st.expander(mermaid_expander_label, expanded=expanded):
                    _render_mermaid(
                        segments[i + 1][1],
                        key=f"{mermaid_key_prefix}_{mermaid_idx}",
                    )
                mermaid_idx += 1
                i += 2
                continue
        else:
            _render_mermaid(chunk, key=f"{mermaid_key_prefix}_{mermaid_idx}")
            mermaid_idx += 1
        i += 1
    return True


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
        st.error("`docs/guides/info.md` was not found.")
        return

    raw = INFO_MD_PATH.read_text(encoding="utf-8")
    title_line = raw.split("\n", 1)[0].lstrip("#").strip() if raw else "Project guide"
    body_text = _body_text_without_title(raw)

    st.markdown(
        f"""
        <div class="info-doc-wrap">
          <div class="info-doc-hero">
            <h1>{html.escape(title_line)}</h1>
            <p>Architecture, flows, and how this app works — rendered from <code>docs/guides/info.md</code>.</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    segments = _split_markdown_and_mermaid(body_text)
    mermaid_idx = 0
    for kind, chunk in segments:
        if kind == "md":
            st.markdown(polish_ui_copy(chunk), unsafe_allow_html=False)
        else:
            _render_mermaid(chunk, key=f"mermaid_{mermaid_idx}")
            mermaid_idx += 1

    st.caption("Tip: Edit `docs/guides/info.md` in the repo and refresh this page to see updates.")
