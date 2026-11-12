"""Smoke tests for info.md splitting used by the /dev docs page."""

from config import PROJECT_ROOT
from services.ui.info_markdown_view import (
    ARCHITECTURE_MD_PATH,
    INFO_MD_PATH,
    _body_text_without_title,
    _image_match_spans,
    _mermaid_iframe_height,
    _resolve_markdown_image,
    _split_markdown_and_mermaid,
    _split_md_images,
    _strip_trailing_section_heading,
)

APPLICATION_FLOWS_MD_PATH = PROJECT_ROOT / "Architecture.md"


def test_info_md_exists_and_splits():
    assert INFO_MD_PATH.is_file()
    raw = INFO_MD_PATH.read_text(encoding="utf-8")
    body = _body_text_without_title(raw)
    assert raw.startswith("#")
    assert not body.lstrip().startswith("# Trip Planner")
    segments = _split_markdown_and_mermaid(body)
    kinds = [k for k, _ in segments]
    assert "mermaid" in kinds
    expected_mermaid = raw.count("```mermaid")
    assert sum(1 for k in kinds if k == "mermaid") == expected_mermaid
    assert len(segments) >= max(1, expected_mermaid)


def test_mermaid_height_bounds():
    h = _mermaid_iframe_height("flowchart TD\n" + "A-->B\n" * 40)
    assert 260 <= h <= 1100


def test_application_flows_md_exists_and_splits_for_dev_page():
    assert APPLICATION_FLOWS_MD_PATH.is_file()
    raw = APPLICATION_FLOWS_MD_PATH.read_text(encoding="utf-8")
    assert "# Application flows" in raw
    segments = _split_markdown_and_mermaid(raw)
    expected_mermaid = raw.count("```mermaid")
    assert sum(1 for k, _ in segments if k == "mermaid") == expected_mermaid
    assert expected_mermaid == 7


def test_architecture_md_flow_diagrams_resolve():
    assert ARCHITECTURE_MD_PATH.is_file()
    raw = ARCHITECTURE_MD_PATH.read_text(encoding="utf-8")
    assert raw.count('class="arch-flow-diagram"') == 4
    spans = _image_match_spans(raw)
    assert len(spans) == 4
    for _start, _end, alt, path in spans:
        resolved = _resolve_markdown_image(ARCHITECTURE_MD_PATH, path)
        assert resolved is not None
        assert resolved.is_file()
        assert alt


def test_split_md_images_arch_flow_block():
    block = (
        '<div class="arch-flow-diagram">'
        '<a class="arch-flow-expand" href="../assets/dev-flows/a.png"></a>'
        '<img src="../assets/dev-flows/a.png" alt="Flow A" />'
        "</div>"
    )
    segments = _split_md_images(f"intro\n\n{block}\n\ntail")
    kinds = [k for k, _ in segments]
    assert kinds.count("image") == 1
    assert "tail" in segments[-1][1]


def test_strip_trailing_section_heading_for_expander():
    body, title = _strip_trailing_section_heading("intro\n\n## Customer Portal → Refund\n")
    assert title == "Customer Portal → Refund"
    assert "##" not in body
    unchanged, no_title = _strip_trailing_section_heading("no heading here")
    assert no_title is None
    assert unchanged == "no heading here"
