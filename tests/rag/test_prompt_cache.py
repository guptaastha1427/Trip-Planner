"""Gemini CachedContent for grounded system prompt — fallback when cache path fails."""

from unittest.mock import MagicMock, patch

from services.rag.website_rag import (
    GROUNDED_SYSTEM_INSTRUCTION,
    RetrievedChunk,
    generate_grounded_answer,
)


def test_prompt_cache_disabled_uses_system_instruction():
    chunk = RetrievedChunk(source="Terms", text="Policy snippet.", score=0.9)
    configs_seen: list = []

    def capture_generate(client, model, *, contents, config):
        configs_seen.append(config)
        resp = MagicMock()
        resp.text = "Grounded reply."
        return model, resp

    with patch("config.is_gemini_prompt_cache_enabled", return_value=False), patch(
        "services.rag.website_rag.get_gemini_api_key", return_value="test-key"
    ), patch(
        "services.rag.website_rag.generate_content_with_fallback", side_effect=capture_generate
    ):
        text, err = generate_grounded_answer("refund?", [chunk])

    assert text == "Grounded reply."
    assert err is None
    assert len(configs_seen) == 1
    assert configs_seen[0].system_instruction == GROUNDED_SYSTEM_INSTRUCTION
    assert not getattr(configs_seen[0], "cached_content", None)


def test_prompt_cache_enabled_falls_back_on_generate_error():
    chunk = RetrievedChunk(source="Terms", text="Policy snippet.", score=0.9)
    configs_seen: list = []
    contents_seen: list = []
    calls = {"n": 0}

    def capture_generate(client, model, *, contents, config):
        calls["n"] += 1
        configs_seen.append(config)
        contents_seen.append(contents)
        if getattr(config, "cached_content", None):
            raise RuntimeError("cached_content rejected")
        resp = MagicMock()
        resp.text = "Fallback reply."
        return model, resp

    with patch("config.is_gemini_prompt_cache_enabled", return_value=True), patch(
        "services.rag.website_rag.get_gemini_api_key", return_value="test-key"
    ), patch(
        "services.rag.website_rag.get_grounded_system_cached_content",
        return_value="cachedContents/abc123",
    ), patch(
        "services.rag.website_rag.generate_content_with_fallback", side_effect=capture_generate
    ):
        text, err = generate_grounded_answer("refund?", [chunk])

    assert text == "Fallback reply."
    assert err is None
    assert calls["n"] == 2
    assert getattr(configs_seen[0], "cached_content", None) == "cachedContents/abc123"
    assert configs_seen[1].system_instruction == GROUNDED_SYSTEM_INSTRUCTION
    user_part = contents_seen[1][0].parts[0].text
    assert "refund?" in user_part
    assert "Policy snippet." in user_part


def test_prompt_cache_create_failure_uses_inline_system():
    chunk = RetrievedChunk(source="Terms", text="Policy snippet.", score=0.9)
    configs_seen: list = []

    def capture_generate(client, model, *, contents, config):
        configs_seen.append(config)
        resp = MagicMock()
        resp.text = "Inline system reply."
        return model, resp

    with patch("config.is_gemini_prompt_cache_enabled", return_value=True), patch(
        "services.rag.website_rag.get_gemini_api_key", return_value="test-key"
    ), patch(
        "services.rag.website_rag.get_grounded_system_cached_content", return_value=None
    ), patch(
        "services.rag.website_rag.generate_content_with_fallback", side_effect=capture_generate
    ):
        text, err = generate_grounded_answer("package pricing?", [chunk])

    assert text == "Inline system reply."
    assert len(configs_seen) == 1
    assert configs_seen[0].system_instruction == GROUNDED_SYSTEM_INSTRUCTION
