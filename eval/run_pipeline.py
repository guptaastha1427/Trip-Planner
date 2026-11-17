#!/usr/bin/env python3
"""
Ragas-aligned + retrieval ranking evaluation pipeline.

Runs golden Terms RAG cases with per-case metrics, failure analysis, and
timestamped artifacts. Does not modify production routes or services.

Usage (repo root, app venv):
  python -m eval.run_pipeline
  python3 -m eval.run_pipeline --k 5 --dataset terms_rag_golden.jsonl
  python3 -m eval.run_pipeline --refresh-baseline
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from eval.runners.ragas_pipeline import (  # noqa: E402
    MetricThresholds,
    run_terms_rag_pipeline,
)
from eval.runners.refund_rules import run_refund_rules_eval  # noqa: E402
from eval.runners.support_faq import run_support_faq_eval  # noqa: E402
from eval.runners.wikivoyage import run_wikivoyage_eval  # noqa: E402
from eval.helpers.run_metadata import run_context_block  # noqa: E402
from eval.helpers.eval_report import write_pipeline_report  # noqa: E402

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def _timestamp_slug() -> str: 
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_payload(
    *,
    thresholds: MetricThresholds,
    dataset: str,
    include_auxiliary: bool,
    refresh_reason: Optional[str] = None,
    baseline: bool = False,
) -> Dict[str, Any]:
    terms = run_terms_rag_pipeline(dataset, thresholds=thresholds) 
    rows = terms["rows"]
    payload: Dict[str, Any] = {
        "pipeline": "eval.run_pipeline",
        "phase": "baseline_assessment",
        "generated_at": datetime.now(timezone.utc).isoformat(), 
        "dataset": dataset,
        "datasets_dir": "eval/datasets",
        "thresholds": thresholds.to_dict(),
        **run_context_block(rows, refresh_reason=refresh_reason, baseline=baseline),
        "summary": {
            "terms_rag_pipeline": terms["summary"],
        },
        "cases": {
            "terms_rag": rows,
        },
    }
    if include_auxiliary:
        payload["summary"]["support_faq"] = run_support_faq_eval()["summary"]
        payload["summary"]["wikivoyage"] = run_wikivoyage_eval()["summary"]
        payload["summary"]["refund_rules"] = run_refund_rules_eval()["summary"]
    return payload


def write_artifact(
    payload: dict,
    *,
    stamp: Optional[str] = None,
    prefix: str = "evaluation_run",
) -> Path:
    """Write timestamped JSON under eval/artifacts/ (gitignored)."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = stamp or _timestamp_slug()
    safe_prefix = prefix.strip().rstrip("_") or "evaluation_run"
    path = ARTIFACTS_DIR / f"{safe_prefix}_{stamp}.json"
    payload = {
        **payload,
        "artifact": {
            "filename": path.name,
            "prefix": safe_prefix,
            "timestamp_utc": stamp,
        },
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary_csv(path, payload)
    return path


def write_summary_csv(json_path: Path, payload: dict) -> Optional[Path]: 
    """Write a one-row CSV companion for spreadsheet / dashboard use."""
    import csv

    s = (payload.get("summary") or {}).get("terms_rag_pipeline") or {}
    if not s:
        return None
    csv_path = json_path.with_suffix(".csv")
    canon = s.get("ragas_canonical_mean") or {}
    row = {
        "generated_at": payload.get("generated_at", ""),
        "evaluation_mode": payload.get("evaluation_mode", ""),
        "retrieval_profile": (payload.get("retrieval_profile") or {}).get("profile_id", ""),
        "embedding_mode": s.get("embedding_mode", ""),
        "mrr_mean": s.get("mrr_mean"),
        "hit_rate_at_3": s.get("hit_rate_at_3"),
        "ndcg_at_3_mean": s.get("ndcg_at_3_mean"),
        "faithfulness": canon.get("faithfulness"),
        "answer_relevance": canon.get("answer_relevance"),
        "context_precision": canon.get("context_precision"),
        "context_recall": canon.get("context_recall"),
        "pass_rate": s.get("pass_rate"),
    }
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)
    if isinstance(payload.get("artifact"), dict):
        payload["artifact"]["summary_csv"] = csv_path.name
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return csv_path


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace: 
    p = argparse.ArgumentParser(description="Ragas + retrieval evaluation pipeline")
    p.add_argument(
        "--dataset",
        default="terms_rag_golden.jsonl",
        help="Golden JSONL under eval/datasets/",
    )
    p.add_argument("--k", type=int, default=3, help="Top-K for Hit/NDCG reporting")
    p.add_argument(
        "--min-answer-correctness",
        type=float,
        default=0.35,
        help="Failure threshold for answer_correctness",
    )
    p.add_argument(
        "--min-ndcg",
        type=float,
        default=0.0,
        help="Failure threshold for NDCG@K (0 = report only)",
    )
    p.add_argument(
        "--auxiliary",
        action="store_true",
        help="Also run support FAQ, wikivoyage, refund summaries",
    )
    p.add_argument(
        "--output-stamp",
        default="",
        help="Override artifact timestamp suffix",
    )
    p.add_argument(
        "--baseline",
        action="store_true",
        help="Write baseline_YYYYMMDDTHHMMSSZ.json (regression tracking name)",
    )
    p.add_argument(
        "--refresh-baseline",
        action="store_true",
        help="Shorthand: --baseline --auxiliary --refresh-reason post_hybrid_retrieval",
    )
    p.add_argument(
        "--refresh-reason",
        default="",
        help="Recorded in artifact_lineage (e.g. post_hybrid_retrieval)",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Also write eval/reports/EVAL_REPORT.md from this run",
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.refresh_baseline:
        args.baseline = True
        args.auxiliary = True
        args.report = args.report or True
        if not args.refresh_reason:
            args.refresh_reason = "post_hybrid_retrieval"
    thresholds = MetricThresholds(
        k=args.k,
        ndcg_at_k=args.min_ndcg,
        answer_correctness=args.min_answer_correctness,
    )
    payload = build_payload(
        thresholds=thresholds,
        dataset=args.dataset,
        include_auxiliary=args.auxiliary or args.refresh_baseline,
        refresh_reason=args.refresh_reason or None,
        baseline=bool(args.baseline),
    )
    stamp = args.output_stamp or _timestamp_slug()
    artifact_prefix = "baseline" if args.baseline else "evaluation_run"
    path = write_artifact(payload, stamp=stamp, prefix=artifact_prefix)
    s = payload["summary"]["terms_rag_pipeline"]
    rk = s["retrieval_k"]
    hit_key = f"hit_rate_at_{rk}"
    ndcg_key = f"ndcg_at_{rk}_mean"
    canon = s.get("ragas_canonical_mean") or {}
    csv_path = path.with_suffix(".csv")
    print(f"Wrote {path}")
    if csv_path.exists():
        print(f"Wrote {csv_path}")
    print(f"evaluation_mode={payload.get('evaluation_mode')} profile={payload.get('retrieval_profile', {}).get('profile_id')}")
    print(
        f"Terms RAG: {s['passed']}/{s['total_cases']} passed | "
        f"MRR={s['mrr_mean']} Hit@{rk}={s.get(hit_key)} NDCG@{rk}={s.get(ndcg_key)} | "
        f"faithfulness={canon.get('faithfulness')} "
        f"answer_relevance={canon.get('answer_relevance')} "
        f"context_precision={canon.get('context_precision')} "
        f"context_recall={canon.get('context_recall')}"
    )
    if args.report:
        report_path = write_pipeline_report(
            payload, project_root=PROJECT, artifact_path=path.resolve()
        )
        print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
