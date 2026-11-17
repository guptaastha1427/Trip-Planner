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

RAGAS_PER_CASE_FLOWCHART_LINES = [
    "",
    "## Appendix — Terms RAG pipeline (per golden case)",
    "",
    "Run: `python -m eval.run_pipeline` (default dataset: `eval/datasets/terms_rag_golden.jsonl`).",
    "Each JSONL row runs retrieve → answer → score → pass/fail; summary and artifact are written once after all rows.",
    "Add `--auxiliary` to include Support FAQ, Wikivoyage, and Refund evals in the same artifact (not in this loop).",
    "",
    "```mermaid",
    "flowchart TB",
    '  START(["Run eval<br/>python -m eval.run_pipeline"])',
    '  DATA["Load golden questions<br/>eval/datasets/terms_rag_golden.jsonl"]',
    "  START --> DATA",
    "",
    '  DATA --> LOOP{{"Each test question"}}',
    "",
    '  LOOP --> RET["Retrieve policy chunks<br/>FAISS over Terms & Policies<br/>eval: HuggingFace index, cache OFF"]',
    '  RET --> ANS["Build answer<br/>answer_from_terms_document<br/>(same path as Policy / Support bot)"]',
    "",
    '  ANS --> GEN_OK{"Answer produced?"}',
    '  GEN_OK -->|No| FAIL["Case FAILED + reason"]',
    '  GEN_OK -->|Yes| SCORE["Score this case"]',
    "",
    '  SCORE --> R["Retrieval metrics<br/>MRR, Hit@K, NDCG<br/>vs expected_sources"]',
    '  SCORE --> Q["Answer quality<br/>keywords, citations, groundedness<br/>(Ragas-style metrics)"]',
    "",
    '  R --> DECIDE{"Meets thresholds?"}',
    "  Q --> DECIDE",
    "",
    '  DECIDE -->|Yes| OK["Case PASSED"]',
    '  DECIDE -->|No| FAIL',
    "",
    "  OK --> NEXT",
    "  FAIL --> NEXT",
    '  NEXT{{"Another row in JSONL?"}}',
    "  NEXT -->|Yes| LOOP",
    '  NEXT -->|No| SUM["Summary<br/>pass rate, average scores"]',
    "",
    '  SUM --> SAVE["Save artifact<br/>eval/artifacts/*.json (+ optional .csv / report)"]',
    "",
    '  AUX["Optional: --auxiliary<br/>support_faq, wikivoyage, refund_rules"]',
    "  SAVE -.-> AUX",
    "```",
    "",
]

ARTIFACTS_FOLDER_REFERENCE_LINES = [
    "",
    "## Appendix — `eval/artifacts/` files (reference)",
    "",
    "New runs add timestamped `evaluation_run_*.json` or `baseline_*.json` (often gitignored).",
    "Look for Ragas eval under `summary.terms_rag_pipeline` / `cases.terms_rag`;",
    "Support / Wikivoyage / Refund under `summary.support_faq`, `summary.wikivoyage`, `summary.refund_rules`.",
    "",
    "| File | Source / type | What's inside |",
    "|------|----------------|---------------|",
    "| **`baseline_20261112T105743Z.json`** | `run_pipeline --refresh-baseline` | **All four:** Ragas Terms RAG (`cases.terms_rag[]`) + support_faq + wikivoyage + refund summaries |",
    "| **`baseline_20261112T092643Z.json`** | Full baseline run | Same — Ragas pipeline + support + wikivoyage + refund |",
    "| **`evaluation_run_real_embeddings.json`** | `run_pipeline` (no `--auxiliary`) | **Ragas / Terms only** — no support / wikivoyage / refund |",
    "| **`baseline_20261112T092947Z.json`** | Legacy `run_baseline.py` | **Not Ragas:** `terms_retrieval` + `terms_generation`, support, wikivoyage, refund, `min_relevance_sweep` |",
    "| **`baseline_20261112T105743Z.csv`** | Companion to `105743Z.json` | **One row** — Terms RAG / Ragas means only (MRR, Hit@3, faithfulness, pass_rate, …) |",
    "",
]

RAGAS_ARCHITECTURE_MMD = REPORTS_DIR / "ragas_pipeline_architecture.mmd"


def ragas_detailed_architecture_lines() -> List[str]:
    """Detailed Mermaid architecture (maintained in eval/reports/ragas_pipeline_architecture.mmd)."""
    if not RAGAS_ARCHITECTURE_MMD.is_file():
        return []
    body = RAGAS_ARCHITECTURE_MMD.read_text(encoding="utf-8").strip()
    return [
        "",
        "## Appendix — RAGAS pipeline architecture (detailed)",
        "",
        "Code path: `eval/run_pipeline.py` → `eval/runners/ragas_pipeline.py`.",
        "Diagram source: `eval/reports/ragas_pipeline_architecture.mmd`.",
        "",
        "```mermaid",
        body,
        "```",
        "",
]

AUXILIARY_EVAL_WORKFLOWS_LINES = [
    "",
    "## Appendix — Auxiliary eval workflows (Support, Wikivoyage, Refund)",
    "",
    "Triggered by `python -m eval.run_pipeline --auxiliary`, `run_baseline.py`, or `pytest tests/eval/`.",
    "Bundled into the same artifact as Terms RAG when `--auxiliary` or `--refresh-baseline` is used.",
    "",
    "### 1. `support_faq_routing.jsonl` → `run_support_faq_eval()`",
    "",
    "**Runner:** `eval/runners/support_faq.py`",
    "",
    "| Step | What happens |",
    "|------|----------------|",
    "| 1 | Load row: `user_id`, `message`, `expected_route`, `expect_escalate` |",
    "| 2 | Patch `answer_from_terms_document` to count RAG calls and run real Terms RAG with eval FAISS (HuggingFace) |",
    "| 3 | Call production `answer_support_query(user_id, message)` (greeting, account, refund status, booking BK-…, or terms RAG) |",
    "| 4 | `_classify_route` on message + reply + RAG call count → `actual_route` (e.g. `terms_rag`, `booking_lookup`) |",
    "| 5 | Compare `actual_route` to `expected_route` (small relaxations for `terms_rag` / `no_match_or_loose`) |",
    "| 6 | Escalation: for most routes, `escalate` must match `expect_escalate`; greeting/empty/booking/refund_status → routing only |",
    "| 7 | Aggregate: `routing_accuracy`, `pass_rate` |",
    "",
    "**Pass** = correct branch (+ escalation when required). Does **not** grade answer text quality.",
    "",
    "### 2. `wikivoyage_golden.jsonl` → `run_wikivoyage_eval()`",
    "",
    "**Runner:** `eval/runners/wikivoyage.py` · Default mode: **`mocked_wikivoyage_html`** (no real HTTP).",
    "",
    "| Step | What happens |",
    "|------|----------------|",
    "| 1 | Load row: `destination`, `query`, `expected_keywords`, `min_chunks`, `expect_ok`, … |",
    "| 2 | Clear `_RAG_CACHE` |",
    "| 3 | Patch `_fetch_wikivoyage_article` → fake HTML for that city (or `None` for bad titles) |",
    "| 4 | `retrieve_guides(..., enabled=True)` → TF-IDF build/search → chunks + scores |",
    "| 5 | `retrieve_guides(..., enabled=False)` → must return **no chunks** |",
    "| 6 | Check: `ok`, chunk count ≥ `min_chunks`, keywords appear in chunk text (or destination) |",
    "| 7 | Aggregate: `pass_rate`, `mode: mocked_wikivoyage_html` |",
    "",
    "Optional: `EVAL_LIVE=1` + `live_network=True` → real API; logs `ok` + chunk count only.",
    "",
    "**Pass** = retrieval behaves when RAG is on and off; optional keyword/chunk checks.",
    "",
    "### 3. `refund_decision_table.jsonl` → `run_refund_rules_eval()`",
    "",
    "**Runner:** `eval/runners/refund_rules.py` · **No RAG, no LLM.**",
    "",
    "| Step | What happens |",
    "|------|----------------|",
    "| 1 | Load row: `booking_id`, `user_id`, `now`, `account_status`, `reason`, `expected_eligibility`, optional refund bounds |",
    "| 2 | `get_booking(booking_id)` from demo portal data |",
    "| 3 | If missing → pass only if case expects `missing_booking` error |",
    "| 4 | `evaluate_refund_request(...)` — pure rules (policy, timing, fees) |",
    "| 5 | Compare `ev.eligibility` to `expected_eligibility`; optional min/max `estimated_refund` |",
    "| 6 | Aggregate: `pass_rate` |",
    "",
    "**Pass** = rule engine output matches the golden row.",
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
    lines.extend(RAGAS_PER_CASE_FLOWCHART_LINES)
    lines.extend(ARTIFACTS_FOLDER_REFERENCE_LINES)
    lines.extend(ragas_detailed_architecture_lines())
    lines.extend(AUXILIARY_EVAL_WORKFLOWS_LINES)

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
        *RAGAS_PER_CASE_FLOWCHART_LINES,
        *ARTIFACTS_FOLDER_REFERENCE_LINES,
        *ragas_detailed_architecture_lines(),
        *AUXILIARY_EVAL_WORKFLOWS_LINES,
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
