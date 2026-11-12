"""Optional ragas library integration (install ragas + EVAL_LIVE for full Ragas)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from eval.evaluators.llm_judge import is_live_judge_enabled


def is_ragas_library_enabled() -> bool:
    """Official Ragas metrics when package installed and live eval requested."""
    if not is_live_judge_enabled():
        return False
    return os.environ.get("EVAL_RAGAS", "1").strip().lower() in ("1", "true", "yes", "")


def try_ragas_evaluate(
    question: str,
    answer: str,
    contexts: List[str],
    reference: str,
) -> Optional[Dict[str, float]]:
    """
    Run ragas metrics when the package is installed and an LLM is configured.
    Returns None when ragas is unavailable or evaluation fails.
    """
    try:
        from ragas import evaluate  # type: ignore
        from ragas.metrics import (  # type: ignore
            answer_correctness,
            context_precision,
            faithfulness,
        )
        from datasets import Dataset  # type: ignore
    except ImportError:
        return None

    try:
        ds = Dataset.from_dict(
            {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
                "ground_truth": [reference],
            }
        )
        result = evaluate(
            ds,
            metrics=[faithfulness, answer_correctness, context_precision],
        )
        row = result.to_pandas().iloc[0]
        return {
            "answer_correctness": float(row.get("answer_correctness", 0)),
            "context_utilization": float(row.get("context_precision", 0)),
            "groundedness": float(row.get("faithfulness", 0)),
            "hallucination_rate": round(
                max(0.0, 1.0 - float(row.get("faithfulness", 0))), 4
            ),
        }
    except Exception:
        return None
