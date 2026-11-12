"""Shared Markdown report for eval artifacts (pipeline + legacy baseline)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"
REPORT_FILENAME = "EVAL_REPORT.md"

EVAL_FLOWCHART_LINES = [
    "",
    "### High-level eval flow",
    "",
    "```mermaid",
    "flowchart TB",
    '  subgraph datasets["Golden data"]',
    "    D1[terms_rag_golden.jsonl]",
    "    D2[support_faq_routing.jsonl]",
    "    D3[wikivoyage_golden.jsonl]",
    "    D4[refund_decision_table.jsonl]",
    "  end",
    "",
    '  subgraph entry["Entry points (use one refresh path)"]',
    "    PY[pytest tests/eval/]",
    "    PL[python3 -m eval.run_pipeline --refresh-baseline --report]",
    "    LEG[python -m eval — sweep + legacy JSON only]",
    "  end",
    "",
    '  subgraph runners["runners/"]',
    "    RP[ragas_pipeline Terms RAG]",
    "    TR[terms_retrieval]",
    "    TG[terms_generation]",
    "    SF[support_faq]",
    "    WV[wikivoyage]",
    "    RF[refund_rules]",
    "  end",
    "",
    '  subgraph out["Outputs"]',
    "    ART[artifacts/baseline_*.json + .csv]",
    "    RPT[reports/EVAL_REPORT.md]",
    "  end",
    "",
    "  datasets --> runners",
    "  PY --> runners",
    "  PL --> RP",
    "  PL --> ART",
    "  PL --> RPT",
    "  LEG --> TR",
    "  LEG --> TG",
    "  LEG --> ART",
    "  RP --> SF",
    "  RP --> WV",
    "  RP --> RF",
    "```",
    "",
]

STATUS_LEGEND = [
    "## Status legend",
    "- **Passed** / **Failed** — automated eval result",
    "- **Requires API credentials** — set `EVAL_LIVE=1` and `GEMINI_API_KEY` for live embed/judge",
    "- **Requires human review** — complex policy interpretation",
    "",
]


def _failed_terms_ids(payload: dict) -> List[str]:
    rows = (payload.get("cases") or {}).get("terms_rag") or []
    return [
        str(r.get("test_id"))
        for r in rows
        if r.get("passed") is False and r.get("test_id")
    ]


def _artifact_ref(project_root: Path, artifact_path: Optional[Path]) -> str:
    if artifact_path is None:
        return "`eval/artifacts/baseline_*.json`"
    try:
        return f"`{artifact_path.relative_to(project_root)}`"
    except ValueError:
        return f"`{artifact_path}`"


def write_pipeline_report(
    payload: dict,
    *,
    project_root: Path,
    artifact_path: Optional[Path] = None,
) -> Path:
    """Human-readable report from eval.run_pipeline payload."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / REPORT_FILENAME
    s = (payload.get("summary") or {}).get("terms_rag_pipeline") or {}
    rk = s.get("retrieval_k", 3)
    hit_key = f"hit_rate_at_{rk}"
    ndcg_key = f"ndcg_at_{rk}_mean"
    canon = s.get("ragas_canonical_mean") or {}
    profile = payload.get("retrieval_profile") or {}
    failed = _failed_terms_ids(payload)

    lines: List[str] = [
        "# Travel Planner — Evaluation Report",
        "",
        f"_Generated: {payload.get('generated_at', '')}_",
        f"_Source: `eval.run_pipeline` · `evaluation_mode`: **{payload.get('evaluation_mode', 'unknown')}**_",
        "",
        *STATUS_LEGEND,
        "## 1. Architecture (verified)",
        "Separate stacks: Terms FAISS+Gemini, Support FAQ rules+RAG, Wikivoyage TF-IDF, Refund rules engine.",
        *EVAL_FLOWCHART_LINES,
        "## 2. Terms / Policy RAG (pipeline — retrieval + generation)",
        f"- Retrieval profile: **{profile.get('profile_id', 'n/a')}** (hybrid={profile.get('hybrid_enabled')})",
        f"- Embedding (eval): {s.get('embedding_mode', 'n/a')}",
        f"- Cases: {s.get('total_cases')} · passed: {s.get('passed')}/{s.get('total_cases')} (rate {s.get('pass_rate')})",
        f"- MRR: {s.get('mrr_mean')}",
        f"- Hit@{rk}: {s.get(hit_key)}",
        f"- NDCG@{rk}: {s.get(ndcg_key)}",
        f"- Answer correctness (mean): {s.get('answer_correctness_mean')}",
        f"- Context utilization (mean): {s.get('context_utilization_mean')}",
        f"- Groundedness (mean): {s.get('groundedness_mean')}",
        f"- Hallucination rate (mean): {s.get('hallucination_rate_mean')}",
        "",
        "### Ragas-aligned means (offline mapping unless `EVAL_LIVE` + ragas)",
        f"- Faithfulness: {canon.get('faithfulness')}",
        f"- Answer relevance: {canon.get('answer_relevance')}",
        f"- Context precision: {canon.get('context_precision')}",
        f"- Context recall: {canon.get('context_recall')}",
        "",
    ]

    if "support_faq" in (payload.get("summary") or {}):
        sup = payload["summary"]["support_faq"]
        lines.extend(
            [
                "## 3. Support FAQ routing",
                f"- Routing accuracy: {sup.get('routing_accuracy')}",
                f"- Pass rate: {sup.get('pass_rate')} ({sup.get('passed')}/{sup.get('total')})",
                "",
            ]
        )
    if "wikivoyage" in (payload.get("summary") or {}):
        w = payload["summary"]["wikivoyage"]
        lines.extend(
            [
                "## 4. Wikivoyage RAG",
                f"- Mode: {w.get('mode')}",
                f"- Pass rate: {w.get('pass_rate')} ({w.get('passed')}/{w.get('total')})",
                "",
            ]
        )
    if "refund_rules" in (payload.get("summary") or {}):
        r = payload["summary"]["refund_rules"]
        lines.extend(
            [
                "## 5. Refund rules engine",
                f"- Pass rate: {r.get('pass_rate')} ({r.get('passed')}/{r.get('total')})",
                "",
            ]
        )

    lines.extend(
        [
            "## 6. Threshold experiment (legacy baseline only)",
            "Run `python3 -m eval` (`run_baseline.py`) for `experiments.min_relevance_sweep` in a separate JSON artifact.",
            "",
            "## 7. LLM-as-Judge / official Ragas",
            f"- `official_ragas_requested`: {payload.get('official_ragas_requested')}",
            "- Live: `EVAL_LIVE=1`, `pip install -r eval/requirements-eval.txt`, optional `EVAL_RAGAS=0` for judge-only.",
            "",
            "## 8. Production vs eval embeddings",
            "Eval defaults to HuggingFace MiniLM; production Terms path uses Gemini embeddings unless `EVAL_EMBEDDINGS=gemini`.",
            "",
            f"Full JSON artifact: {_artifact_ref(project_root, artifact_path)}",
            "",
            "## Failure analysis",
        ]
    )
    if failed:
        lines.append(f"- Failed Terms cases: {', '.join(failed)}")
        lines.append("- Inspect per-case `failure_analysis` in the JSON artifact.")
    else:
        lines.append("- All Terms pipeline cases passed configured thresholds.")
    lines.append("- Per-case detail: `cases.terms_rag[]` in the artifact JSON.")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def write_legacy_baseline_report(
    payload: dict,
    *,
    project_root: Path,
    artifact_path: Optional[Path] = None,
) -> Path:
    """Report from run_baseline.py payload (split retrieval / generation)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORTS_DIR / REPORT_FILENAME
    s = payload.get("summary") or {}

    lines = [
        "# Travel Planner — Evaluation Report",
        "",
        f"_Generated: {payload.get('generated_at', '')}_",
        "_Source: `run_baseline.py` (legacy — prefer `run_pipeline --refresh-baseline --report`)_",
        "",
        *STATUS_LEGEND,
        "## 1. Architecture (verified)",
        "Separate stacks: Terms FAISS+Gemini, Support FAQ rules+RAG, Wikivoyage TF-IDF, Refund rules engine.",
        *EVAL_FLOWCHART_LINES,
        "## 2. Terms / Policy RAG — retrieval (HuggingFace eval embeddings)",
        f"- Cases: {s['terms_retrieval']['total_cases']}",
        f"- Hit@1: {s['terms_retrieval'].get('hit_at_1')}",
        f"- Hit@3: {s['terms_retrieval'].get('hit_at_3')}",
        f"- Recall@3: {s['terms_retrieval'].get('recall_at_3')}",
        f"- MRR: {s['terms_retrieval'].get('mrr')}",
        f"- Avg top-1 score: {s['terms_retrieval'].get('avg_top1_score')}",
        f"- Low-confidence %: {s['terms_retrieval'].get('low_confidence_pct')}",
        f"- Escalation accuracy: {s['terms_retrieval'].get('escalation_accuracy')}",
        "",
        "## 3. Terms / Policy RAG — generation (markdown fallback, no Gemini)",
        f"- Pass rate: {s['terms_generation']['pass_rate']} ({s['terms_generation']['passed']}/{s['terms_generation']['total']})",
        "",
        "## 4. Support FAQ routing",
        f"- Routing accuracy: {s['support_faq']['routing_accuracy']}",
        f"- Pass rate: {s['support_faq']['pass_rate']}",
        "",
        "## 5. Wikivoyage RAG",
        f"- Mode: {s['wikivoyage']['mode']}",
        f"- Pass rate: {s['wikivoyage']['pass_rate']}",
        "",
        "## 6. Refund rules engine",
        f"- Pass rate: {s['refund_rules']['pass_rate']}",
        "",
        "## 7. Threshold experiment (eval harness)",
        "See artifact JSON `experiments.min_relevance_sweep`.",
        "",
        "## 8. LLM-as-Judge",
        "**Not tested** in baseline (requires `EVAL_LIVE=1`). Prompt: `eval/evaluators/llm_judge.py`.",
        "",
        "## 9. Live Gemini embeddings",
        "Eval harness uses HuggingFace MiniLM; production Streamlit path uses Gemini embeddings.",
        "",
        f"Full JSON artifact: {_artifact_ref(project_root, artifact_path)}",
        "",
        "## Failure analysis",
        "Inspect `eval/artifacts/baseline_*.json` `details.*_rows` where `pass` is false.",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def write_eval_report(
    payload: dict,
    *,
    project_root: Path,
    artifact_path: Optional[Path] = None,
) -> Path:
    """Pick report template from payload shape."""
    if payload.get("pipeline") == "eval.run_pipeline":
        return write_pipeline_report(
            payload, project_root=project_root, artifact_path=artifact_path
        )
    if "terms_retrieval" in (payload.get("summary") or {}):
        return write_legacy_baseline_report(
            payload, project_root=project_root, artifact_path=artifact_path
        )
    raise ValueError("Unknown eval payload shape for EVAL_REPORT.md")


def is_pipeline_payload(payload: dict) -> bool:
    return payload.get("pipeline") == "eval.run_pipeline"
