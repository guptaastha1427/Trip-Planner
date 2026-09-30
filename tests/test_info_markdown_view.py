"""Smoke tests for info.md splitting used by the /dev docs page."""

from services.info_markdown_view import (
    INFO_MD_PATH,
    _body_text_without_title,
    _mermaid_iframe_height,
    _split_markdown_and_mermaid,
)


def test_info_md_exists_and_splits():
    assert INFO_MD_PATH.is_file()
    raw = INFO_MD_PATH.read_text(encoding="utf-8")
    body = _body_text_without_title(raw)
    assert raw.startswith("#")
    assert not body.lstrip().startswith("# Trip Planner")
    segments = _split_markdown_and_mermaid(body)
    kinds = [k for k, _ in segments]
    assert "mermaid" in kinds
    assert sum(1 for k in kinds if k == "mermaid") == 19
    assert len(segments) >= 20


def test_mermaid_height_bounds():
    h = _mermaid_iframe_height("flowchart TD\n" + "A-->B\n" * 40)
    assert 240 <= h <= 920
