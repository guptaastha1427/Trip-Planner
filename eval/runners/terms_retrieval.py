"""Terms / Policy RAG retrieval evaluation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import patch

from langchain_community.embeddings import FakeEmbeddings

from eval.evaluators.retrieval_metrics import (
    aggregate_retrieval_rows,
    hit_at_k,
    mean_reciprocal_rank,
    recall_at_k,
)
from eval.helpers.io import load_jsonl
from eval.helpers.terms_retrieval import (
    chunk_preview,
    passes_min_score,
    raw_similarity_ranked,
    source_matches,
)
from services.rag.terms_rag import answer_from_terms_document, retrieve_policy_chunks
from services.rag.website_rag import (
    MIN_RELEVANCE_SCORE,
    _terms_source_documents,
    build_faiss_index,
    chunks_to_context,
    retrieve_from_terms_kb,
)


def fake_terms_store():
    return build_faiss_index(_terms_source_documents(), FakeEmbeddings(size=384))


def evaluate_terms_retrieval_row(
    case: Dict[str, Any],
    *,
    top_k: int = 4,
    min_score: float = MIN_RELEVANCE_SCORE,
    raw_k: int = 10,
) -> Dict[str, Any]:
    test_id = case["test_id"]
    question = case["question"]
    expected_sources = case.get("expected_sources") or []
    expect_escalate = bool(case.get("expect_escalate"))

    store = fake_terms_store()
    with patch("services.rag.website_rag.get_terms_vector_store", return_value=store):
        raw = raw_similarity_ranked(question, store, top_k=raw_k)
        raw_sources = [c.source for c in raw]

        with patch("services.rag.website_rag.MIN_RELEVANCE_SCORE", min_score):
            kb_chunks, err = retrieve_from_terms_kb(
                question, top_k=top_k, allow_semantic_cache=False
            )
        filtered_sources = [c.source for c in kb_chunks]

        policy_hits = retrieve_policy_chunks(question, top_k=top_k, min_score=min_score)

    top1_score = raw[0].score if raw else 0.0
    low_confidence = not raw or top1_score < (min_score + 0.08)

    predicted_escalate = not policy_hits or low_confidence
    if expected_sources:
        escalation_match = predicted_escalate == expect_escalate
    else:
        escalation_match = expect_escalate == (not policy_hits or len(filtered_sources) == 0)

    row: Dict[str, Any] = {
        "test_id": test_id,
        "question": question,
        "expected_sources": expected_sources,
        "retrieved": [
            {
                "rank": i,
                "source": c.source,
                "score": round(c.score, 4),
                "passes_min_score": passes_min_score(c.score, min_score),
                "preview": chunk_preview(c.text),
            }
            for i, c in enumerate(raw, start=1)
        ],
        "filtered_sources": filtered_sources,
        "hit_at_1": hit_at_k(expected_sources, raw_sources, 1) if expected_sources else None,
        "hit_at_3": hit_at_k(expected_sources, raw_sources, 3) if expected_sources else None,
        "recall_at_3": recall_at_k(expected_sources, raw_sources, 3) if expected_sources else None,
        "mrr": mean_reciprocal_rank(expected_sources, raw_sources) if expected_sources else None,
        "top1_score": round(top1_score, 4),
        "low_confidence": low_confidence,
        "expect_escalate": expect_escalate,
        "predicted_escalate": predicted_escalate,
        "escalation_match": escalation_match,
        "retrieve_error": err,
        "pass": (
            (hit_at_k(expected_sources, raw_sources, 3) if expected_sources else True)
            and escalation_match
        ),
    }
    return row


def run_terms_retrieval_eval(
    dataset_name: str = "terms_rag_golden.jsonl",
) -> Dict[str, Any]:
    cases = load_jsonl(dataset_name)
    rows = [evaluate_terms_retrieval_row(c) for c in cases]
    labeled = [r for r in rows if r.get("hit_at_3") is not None]
    agg = aggregate_retrieval_rows(labeled)
    esc_rows = [r for r in rows if r.get("escalation_match") is not None]
    esc_acc = sum(1 for r in esc_rows if r["escalation_match"]) / max(len(esc_rows), 1)
    summary = agg.to_dict()
    summary["escalation_accuracy_all_cases"] = round(esc_acc, 4)
    summary["labeled_cases"] = len(labeled)
    summary["total_cases"] = len(rows)
    return {"summary": summary, "rows": rows}


def evaluate_terms_generation_row(
    case: Dict[str, Any],
    *,
    min_score: float = 0.0,
) -> Dict[str, Any]:
    from eval.evaluators.code_checks import generation_code_score

    store = fake_terms_store()
    with patch("services.rag.website_rag.get_terms_vector_store", return_value=store), patch(
        "services.rag.website_rag.MIN_RELEVANCE_SCORE", min_score
    ), patch("services.rag.website_rag.get_gemini_api_key", return_value=None):
        out = answer_from_terms_document(case["question"], min_score=min_score)

    if not out:
        return {
            "test_id": case["test_id"],
            "pass": False,
            "error": "no_answer",
        }
    reply, escalate, sources = out
    code = generation_code_score(
        reply,
        expected_keywords=case.get("expected_keywords") or [],
        require_citation=True,
    )
    with patch("services.rag.website_rag.get_terms_vector_store", return_value=store):
        chunks, _ = retrieve_from_terms_kb(case["question"], allow_semantic_cache=False)
    context = chunks_to_context(chunks[:3]) if chunks else ""

    return {
        "test_id": case["test_id"],
        "reply_preview": reply[:400],
        "escalate": escalate,
        "expect_escalate": case.get("expect_escalate"),
        "sources_count": len(sources),
        "code_checks": code,
        "context_preview": context[:500],
        "pass": code["passed"]
        and (
            case.get("expect_escalate") is None
            or escalate == case.get("expect_escalate")
        ),
    }


def run_terms_generation_eval(dataset_name: str = "terms_rag_golden.jsonl") -> Dict[str, Any]:
    cases = load_jsonl(dataset_name)
    rows = [evaluate_terms_generation_row(c) for c in cases]
    passed = sum(1 for r in rows if r.get("pass"))
    return {
        "summary": {
            "total": len(rows),
            "passed": passed,
            "pass_rate": round(passed / max(len(rows), 1), 4),
            "mode": "markdown_fallback_no_gemini",
        },
        "rows": rows,
    }
