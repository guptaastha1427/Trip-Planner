"""Eval run metadata for artifacts (retrieval profile, evaluation_mode)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from config import (
    EMBEDDING_CACHE_VERSION,
    get_grounded_generation_temperature,
    get_terms_retrieval_candidate_multiplier,
    is_hybrid_terms_retrieval_enabled,
)
from eval.helpers.real_embeddings import embedding_mode_label
from eval.evaluators.llm_judge import is_live_judge_enabled
from services.rag.website_rag import WEB_CHUNK_OVERLAP, WEB_CHUNK_SIZE

HYBRID_RETRIEVAL_PROFILE = "hybrid_rerank_v1"

# Filenames created before hybrid retrieval shipped — treat as pre-hybrid unless re-run.
LEGACY_PRE_HYBRID_ARTIFACT_NAMES = frozenset(
    {
        "evaluation_run_ci_smoke.json",
        "evaluation_run_real_embeddings.json",
    }
)


def is_official_ragas_requested() -> bool:
    return is_live_judge_enabled() or os.environ.get("EVAL_RAGAS", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def retrieval_profile() -> Dict[str, Any]:
    return {
        "profile_id": HYBRID_RETRIEVAL_PROFILE if is_hybrid_terms_retrieval_enabled() else "faiss_semantic_only",
        "hybrid_enabled": is_hybrid_terms_retrieval_enabled(),
        "candidate_multiplier": get_terms_retrieval_candidate_multiplier(),
        "chunk_size": WEB_CHUNK_SIZE,
        "chunk_overlap": WEB_CHUNK_OVERLAP,
        "embedding_cache_version": EMBEDDING_CACHE_VERSION,
        "embedding_mode": embedding_mode_label(),
        "grounded_answer_temperature": get_grounded_generation_temperature(),
    }


def aggregate_evaluation_mode(case_rows: List[Dict[str, Any]]) -> str: #aggregates the evaluation mode.
    """
    Run-level mode for artifact header.

    heuristic_offline | llm_judge_live | ragas_library | mixed_live
    """
    modes = {
        (r.get("ragas_metrics") or {}).get("evaluation_mode")
        for r in case_rows
    }
    modes.discard(None)
    if not modes:
        return "heuristic_offline"
    if modes == {"heuristic_offline"}:
        return "heuristic_offline"
    if modes == {"ragas_library"}:
        return "ragas_library"
    if modes == {"llm_judge_live"}:
        return "llm_judge_live"
    if "ragas_library" in modes:
        return "mixed_live"
    if "llm_judge_live" in modes:
        return "mixed_live"
    return "heuristic_offline"


def artifact_lineage( #artifact lineage.
    *,
    refresh_reason: Optional[str] = None,
    baseline: bool = False,
) -> Dict[str, Any]:
    note = (
        "Timestamped artifacts replace older local JSON on each run. "
        "Files listed in LEGACY_PRE_HYBRID_ARTIFACT_NAMES (eval/helpers/run_metadata.py) "
        "or generated before hybrid rerank are pre-hybrid references until refreshed with "
        "`python3 -m eval.run_pipeline --refresh-baseline`."
    )
    out: Dict[str, Any] = {
        "pre_hybrid_reference_filenames": sorted(LEGACY_PRE_HYBRID_ARTIFACT_NAMES),
        "note": note,
        "baseline_artifact": baseline,
    }
    if refresh_reason:
        out["refresh_reason"] = refresh_reason
    return out


def run_context_block(
    case_rows: List[Dict[str, Any]],
    *,
    refresh_reason: Optional[str] = None,
    baseline: bool = False,
) -> Dict[str, Any]:
    return {
        "evaluation_mode": aggregate_evaluation_mode(case_rows),
        "official_ragas_requested": is_official_ragas_requested(),
        "retrieval_profile": retrieval_profile(),
        "artifact_lineage": artifact_lineage(
            refresh_reason=refresh_reason, baseline=baseline
        ),
    }
