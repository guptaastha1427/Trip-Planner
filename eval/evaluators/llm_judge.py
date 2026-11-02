"""LLM-as-judge prompts for grounded policy answers (optional live mode)."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

JUDGE_SYSTEM = """You are an evaluation judge for a travel app policy assistant.
Score ONLY using the provided retrieved context and expected criteria.
Do NOT use outside knowledge. If the answer adds facts not supported by context, score faithfulness low.
Respond with JSON only: {"faithfulness":0-5,"groundedness":0-5,"relevance":0-5,"completeness":0-5,"correctness":0-5,"citation_accuracy":0-5,"hallucination":0-5,"overall_pass":true|false,"brief_reason":"..."}
Hallucination score: 5 = no hallucination, 0 = severe fabrication."""


def build_judge_prompt(
    question: str,
    retrieved_context: str,
    expected_criteria: str,
    generated_answer: str,
) -> str:
    return f"""User question:
{question}

Retrieved context (only valid evidence):
{retrieved_context}

Expected answer criteria (rubric):
{expected_criteria}

Generated answer to evaluate:
{generated_answer}

Grade the generated answer. JSON only."""


def is_live_judge_enabled() -> bool:
    return os.environ.get("EVAL_LIVE", "").strip().lower() in ("1", "true", "yes")


def run_llm_judge(
    question: str,
    retrieved_context: str,
    expected_criteria: str,
    generated_answer: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Call Gemini judge when EVAL_LIVE=1 and GEMINI_API_KEY is set.
    Returns (parsed_scores, error_message).
    """
    if not is_live_judge_enabled():
        return None, "EVAL_LIVE not set — judge skipped"

    from config import get_gemini_api_key, DEFAULT_MODEL
    from google import genai
    from google.genai import types

    api_key = get_gemini_api_key()
    if not api_key:
        return None, "GEMINI_API_KEY missing — judge skipped"

    prompt = build_judge_prompt(question, retrieved_context, expected_criteria, generated_answer)
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=JUDGE_SYSTEM,
                temperature=0.0,
                response_mime_type="application/json",
            ),
        )
        text = (response.text or "").strip()
        import json

        return json.loads(text), None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
