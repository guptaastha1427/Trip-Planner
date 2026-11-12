"""Answer-quality metrics (Ragas-aligned fields; heuristic offline, LLM judge live)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from eval.evaluators.code_checks import generation_code_score, keywords_present
from eval.evaluators.llm_judge import is_live_judge_enabled, run_llm_judge
from eval.evaluators.ragas_optional import is_ragas_library_enabled, try_ragas_evaluate

_WORD_RE = re.compile(r"[a-z0-9]{4,}", re.I)


def _token_set(text: str) -> set[str]:
    return {m.group(0).lower() for m in _WORD_RE.finditer(text or "")}


def _context_utilization_score(context: str, expected_keywords: Sequence[str]) -> float:
    if not expected_keywords:
        return 1.0 if (context or "").strip() else 0.0
    hits = sum(1 for kw in expected_keywords if kw and kw.lower() in (context or "").lower())
    return hits / len(expected_keywords)


def _groundedness_heuristic(answer: str, context: str) -> float:
    ctx = _token_set(context)
    ans = _token_set(answer)
    if not ans:
        return 0.0
    if not ctx:
        return 0.0
    overlap = len(ans & ctx)
    return overlap / len(ans)


def _hallucination_rate_heuristic(answer: str, context: str) -> float:
    """Fraction of answer content tokens not supported by context (higher = more hallucination)."""
    grounded = _groundedness_heuristic(answer, context)
    return round(max(0.0, min(1.0, 1.0 - grounded)), 4)


def _answer_correctness_heuristic(
    answer: str,
    context: str,
    *,
    expected_keywords: Sequence[str],
    code_checks: Dict[str, Any],
) -> float:
    parts: List[float] = []
    if code_checks.get("passed"):
        parts.append(1.0)
    else:
        parts.append(0.4 if code_checks.get("keywords_ok") else 0.0)
    parts.append(_context_utilization_score(context, expected_keywords))
    parts.append(1.0 if code_checks.get("citation_ok") else 0.5)
    parts.append(_groundedness_heuristic(answer, context))
    return round(sum(parts) / len(parts), 4)


def _judge_to_ragas_fields(judge: Dict[str, Any]) -> Dict[str, float]:
    def norm(key: str) -> float:
        return round(float(judge.get(key, 0)) / 5.0, 4)

    hallucination_score = float(judge.get("hallucination", 0))
    return {
        "answer_correctness": norm("correctness"),
        "context_utilization": norm("faithfulness"),
        "groundedness": norm("groundedness"),
        "hallucination_rate": round(max(0.0, min(1.0, 1.0 - hallucination_score / 5.0)), 4),
    }


def compute_answer_quality_metrics(
    *,
    question: str,
    answer: str,
    retrieved_context: str,
    expected_keywords: Sequence[str],
    expected_behavior: str = "",
    code_checks: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Return (metrics_dict, judge_error).

    metrics_dict includes answer_correctness, context_utilization,
    hallucination_rate, groundedness, and evaluation_mode.
    """
    checks = code_checks or generation_code_score(
        answer,
        expected_keywords=expected_keywords,
        require_citation=True,
    )
    heuristic = {
        "answer_correctness": _answer_correctness_heuristic(
            answer, retrieved_context, expected_keywords=expected_keywords, code_checks=checks
        ),
        "context_utilization": round(
            _context_utilization_score(retrieved_context, expected_keywords), 4
        ),
        "hallucination_rate": _hallucination_rate_heuristic(answer, retrieved_context),
        "groundedness": round(_groundedness_heuristic(answer, retrieved_context), 4),
        "evaluation_mode": "heuristic_offline",
        "code_checks": checks,
    }

    if not is_live_judge_enabled():
        return heuristic, None

    judge_err: Optional[str] = None
    if is_ragas_library_enabled():
        ragas_lib = try_ragas_evaluate(
            question,
            answer,
            [retrieved_context] if retrieved_context else [],
            expected_behavior,
        )
        if ragas_lib:
            merged = {**heuristic, **ragas_lib}
            merged["evaluation_mode"] = "ragas_library"
            return merged, None

    judge_scores, judge_err = run_llm_judge(
        question,
        retrieved_context,
        expected_criteria=expected_behavior or "Answer from context with citations.",
        generated_answer=answer,
    )
    if judge_scores:
        merged = {**heuristic, **_judge_to_ragas_fields(judge_scores)}
        merged["evaluation_mode"] = "llm_judge_live"
        merged["llm_judge"] = judge_scores
        return merged, judge_err

    return heuristic, judge_err
