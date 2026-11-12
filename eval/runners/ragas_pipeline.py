"""Integrated retrieval + Ragas-aligned generation evaluation for Terms RAG."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence
from unittest.mock import patch

from eval.evaluators.answer_quality import compute_answer_quality_metrics
from eval.evaluators.retrieval_metrics import (
    hit_at_k,
    hit_rate_at_k,
    mean_reciprocal_rank,
    ndcg_at_k,
    recall_at_k,
)
from eval.helpers.io import load_jsonl
from eval.helpers.terms_retrieval import chunk_preview, raw_similarity_ranked
from eval.helpers.real_embeddings import (
    build_terms_vector_store_with_huggingface,
    embedding_mode_label,
)
from services.rag.terms_rag import answer_from_terms_document
from services.rag.website_rag import MIN_RELEVANCE_SCORE, chunks_to_context, retrieve_from_terms_kb


@dataclass
class MetricThresholds:
    hit_at_k: float = 0.0
    ndcg_at_k: float = 0.0
    answer_correctness: float = 0.35
    context_utilization: float = 0.0
    groundedness: float = 0.0
    max_hallucination_rate: float = 1.0
    k: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hit_at_k": self.hit_at_k,
            "ndcg_at_k": self.ndcg_at_k,
            "answer_correctness": self.answer_correctness,
            "context_utilization": self.context_utilization,
            "groundedness": self.groundedness,
            "max_hallucination_rate": self.max_hallucination_rate,
            "k": self.k,
        }


def ragas_canonical_metrics(
    ragas_metrics: Dict[str, Any],
    retrieval_metrics: Dict[str, Any],
    *,
    k: int,
) -> Dict[str, Optional[float]]:
    """
    Stable Ragas-style names for artifacts and regression diffs.

    Offline heuristics map groundedness→faithfulness, answer_correctness→answer_relevance,
    context_utilization→context_precision; context_recall uses retrieval recall@K.
    """
    recall_key = f"recall_at_{k}"
    recall = retrieval_metrics.get(recall_key)
    if recall is None and k != 3:
        recall = retrieval_metrics.get("recall_at_3")
    return {
        "faithfulness": ragas_metrics.get("groundedness"),
        "answer_relevance": ragas_metrics.get("answer_correctness"),
        "context_precision": ragas_metrics.get("context_utilization"),
        "context_recall": round(float(recall), 4) if recall is not None else None,
    }


def _build_failure_analysis(
    *,
    thresholds: MetricThresholds,
    retrieval: Dict[str, Any],
    ragas_metrics: Dict[str, Any],
    generation_error: Optional[str],
) -> str:
    reasons: List[str] = []
    k = thresholds.k

    if generation_error:
        reasons.append(f"Generation error: {generation_error}")

    if retrieval.get("expected_sources"):
        if thresholds.hit_at_k > 0 and retrieval.get(f"hit_at_{k}") is False:
            reasons.append(
                f"Retrieval miss: no expected source in top-{k} "
                f"(MRR={retrieval.get('mrr')}, NDCG@{k}={retrieval.get(f'ndcg_at_{k}')})."
            )
        if thresholds.ndcg_at_k > 0 and (retrieval.get(f"ndcg_at_{k}") or 0) < thresholds.ndcg_at_k:
            reasons.append(
                f"NDCG@{k} {retrieval.get(f'ndcg_at_{k}')} below threshold {thresholds.ndcg_at_k}."
            )
        if (retrieval.get(f"hit_rate_at_{k}") or 0) < thresholds.hit_at_k:
            reasons.append(
                f"Hit@{k} below threshold {thresholds.hit_at_k}."
            )

    ac = float(ragas_metrics.get("answer_correctness") or 0)
    if ac < thresholds.answer_correctness:
        reasons.append(
            f"Answer correctness {ac} below threshold {thresholds.answer_correctness}."
        )

    cu = float(ragas_metrics.get("context_utilization") or 0)
    if cu < thresholds.context_utilization:
        reasons.append(
            f"Context utilization {cu} below threshold {thresholds.context_utilization}."
        )

    gr = float(ragas_metrics.get("groundedness") or 0)
    if gr < thresholds.groundedness:
        reasons.append(f"Groundedness {gr} below threshold {thresholds.groundedness}.")

    hall = float(ragas_metrics.get("hallucination_rate") or 0)
    if hall > thresholds.max_hallucination_rate:
        reasons.append(
            f"Hallucination rate {hall} exceeds max {thresholds.max_hallucination_rate}."
        )

    if not reasons:
        return "All configured metrics met thresholds."
    return " ".join(reasons)


def evaluate_terms_rag_pipeline_row(
    case: Dict[str, Any],
    *,
    thresholds: MetricThresholds,
    top_k: int = 4,
    raw_k: int = 10,
    min_score: float = MIN_RELEVANCE_SCORE,
) -> Dict[str, Any]:
    test_id = case["test_id"]
    question = case["question"]
    expected_sources = case.get("expected_sources") or []
    expected_keywords = case.get("expected_keywords") or []
    expected_behavior = case.get("expected_behavior") or ""
    expect_escalate = bool(case.get("expect_escalate"))
    k = thresholds.k

    store = build_terms_vector_store_with_huggingface()
    with patch("services.rag.website_rag.get_terms_vector_store", return_value=store):
        raw = raw_similarity_ranked(question, store, top_k=raw_k)
        raw_sources = [c.source for c in raw]
        retrieved_contexts = [
            {
                "rank": i,
                "source": c.source,
                "score": round(c.score, 4),
                "text": chunk_preview(c.text, limit=400),
            }
            for i, c in enumerate(raw, start=1)
        ]

        with patch("services.rag.website_rag.MIN_RELEVANCE_SCORE", min_score), patch(
            "services.rag.website_rag.get_gemini_api_key", return_value=None
        ):
            gen_out = answer_from_terms_document(question, min_score=0.0, top_k=top_k)
            kb_chunks, retrieve_err = retrieve_from_terms_kb(
                question, top_k=top_k, allow_semantic_cache=False
            )

    context_text = chunks_to_context(kb_chunks[:top_k]) if kb_chunks else ""
    generation_error: Optional[str] = None
    answer = ""
    escalate = None
    source_meta: List[Dict[str, Any]] = []

    if not gen_out:
        generation_error = "no_answer_from_terms_document"
    else:
        answer, escalate, source_meta = gen_out

    from eval.evaluators.code_checks import generation_code_score

    code_checks = generation_code_score(
        answer,
        expected_keywords=expected_keywords,
        require_citation=bool(answer),
    )
    ragas_metrics, judge_err = compute_answer_quality_metrics(
        question=question,
        answer=answer,
        retrieved_context=context_text,
        expected_keywords=expected_keywords,
        expected_behavior=expected_behavior,
        code_checks=code_checks,
    )
    if judge_err and ragas_metrics.get("evaluation_mode") == "heuristic_offline":
        ragas_metrics["llm_judge_skipped"] = judge_err

    top1_score = raw[0].score if raw else 0.0
    low_confidence = not raw or top1_score < (min_score + 0.08)
    retrieval_metrics = {
        "mrr": round(mean_reciprocal_rank(expected_sources, raw_sources), 4)
        if expected_sources
        else None,
        f"hit_at_{k}": hit_at_k(expected_sources, raw_sources, k) if expected_sources else None,
        f"hit_rate_at_{k}": hit_rate_at_k(expected_sources, raw_sources, k)
        if expected_sources
        else None,
        f"ndcg_at_{k}": round(ndcg_at_k(expected_sources, raw_sources, k), 4)
        if expected_sources
        else None,
        "hit_at_1": hit_at_k(expected_sources, raw_sources, 1) if expected_sources else None,
        "hit_at_3": hit_at_k(expected_sources, raw_sources, 3) if expected_sources else None,
        "recall_at_3": round(recall_at_k(expected_sources, raw_sources, 3), 4)
        if expected_sources
        else None,
        "top1_score": round(top1_score, 4),
        "low_confidence": low_confidence,
        "retrieve_error": retrieve_err,
        "retrieved_sources_ranked": raw_sources[:raw_k],
    }

    failure_analysis = _build_failure_analysis(
        thresholds=thresholds,
        retrieval={**retrieval_metrics, "expected_sources": expected_sources},
        ragas_metrics=ragas_metrics,
        generation_error=generation_error,
    )

    passed = (
        generation_error is None
        and failure_analysis == "All configured metrics met thresholds."
    )

    return {
        "test_id": test_id,
        "suite": "terms_rag",
        "input": {
            "user_query": question,
            "expected_sources": expected_sources,
            "expected_keywords": expected_keywords,
            "expected_behavior": expected_behavior,
            "expect_escalate": expect_escalate,
        },
        "output": {
            "generated_response": answer,
            "escalate": escalate,
            "retrieved_contexts": retrieved_contexts,
            "filtered_context_text": context_text[:2000],
            "citation_sources": source_meta,
        },
        "retrieval_metrics": retrieval_metrics,
        "ragas_metrics": {
            "answer_correctness": ragas_metrics.get("answer_correctness"),
            "context_utilization": ragas_metrics.get("context_utilization"),
            "hallucination_rate": ragas_metrics.get("hallucination_rate"),
            "groundedness": ragas_metrics.get("groundedness"),
            "evaluation_mode": ragas_metrics.get("evaluation_mode"),
            "llm_judge": ragas_metrics.get("llm_judge"),
            "ragas_canonical": ragas_canonical_metrics(
                ragas_metrics, retrieval_metrics, k=k
            ),
        },
        "thresholds_applied": thresholds.to_dict(),
        "passed": passed,
        "failure_analysis": failure_analysis,
    }


def _aggregate_pipeline_rows(rows: List[Dict[str, Any]], *, k: int) -> Dict[str, Any]:
    labeled = [r for r in rows if r["retrieval_metrics"].get(f"hit_at_{k}") is not None]
    n = max(len(labeled), 1)
    mrr = sum(float(r["retrieval_metrics"].get("mrr") or 0) for r in labeled) / n
    hit_k = sum(
        1.0 if r["retrieval_metrics"].get(f"hit_at_{k}") else 0.0 for r in labeled
    ) / n
    ndcg_k = sum(
        float(r["retrieval_metrics"].get(f"ndcg_at_{k}") or 0) for r in labeled
    ) / n

    gen_rows = [r for r in rows if r["output"].get("generated_response") is not None]
    gn = max(len(gen_rows), 1)

    def avg_metric(key: str) -> float:
        return round(
            sum(float(r["ragas_metrics"].get(key) or 0) for r in gen_rows) / gn, 4
        )

    def avg_canonical(key: str) -> Optional[float]:
        vals = [
            r["ragas_metrics"].get("ragas_canonical", {}).get(key)
            for r in rows
            if r["ragas_metrics"].get("ragas_canonical", {}).get(key) is not None
        ]
        if not vals:
            return None
        return round(sum(float(v) for v in vals) / len(vals), 4)

    passed = sum(1 for r in rows if r.get("passed"))
    return {
        "total_cases": len(rows),
        "labeled_retrieval_cases": len(labeled),
        "retrieval_k": k,
        "mrr_mean": round(mrr, 4),
        f"hit_rate_at_{k}": round(hit_k, 4),
        f"ndcg_at_{k}_mean": round(ndcg_k, 4),
        "answer_correctness_mean": avg_metric("answer_correctness"),
        "context_utilization_mean": avg_metric("context_utilization"),
        "hallucination_rate_mean": avg_metric("hallucination_rate"),
        "groundedness_mean": avg_metric("groundedness"),
        "ragas_canonical_mean": {
            "faithfulness": avg_canonical("faithfulness"),
            "answer_relevance": avg_canonical("answer_relevance"),
            "context_precision": avg_canonical("context_precision"),
            "context_recall": avg_canonical("context_recall"),
        },
        "passed": passed,
        "pass_rate": round(passed / max(len(rows), 1), 4),
        "embedding_mode": embedding_mode_label(),
        "evaluation_mode": _summary_evaluation_mode(rows),
    }


def _summary_evaluation_mode(rows: List[Dict[str, Any]]) -> str:
    from eval.helpers.run_metadata import aggregate_evaluation_mode

    return aggregate_evaluation_mode(rows)


def run_terms_rag_pipeline(
    dataset_name: str = "terms_rag_golden.jsonl",
    *,
    thresholds: Optional[MetricThresholds] = None,
) -> Dict[str, Any]:
    thresholds = thresholds or MetricThresholds()
    cases = load_jsonl(dataset_name)
    rows = [evaluate_terms_rag_pipeline_row(c, thresholds=thresholds) for c in cases]
    return {
        "summary": _aggregate_pipeline_rows(rows, k=thresholds.k),
        "thresholds": thresholds.to_dict(),
        "rows": rows,
    }
