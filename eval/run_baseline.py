#!/usr/bin/env python3
"""Run baseline evaluation suites and write JSON + Markdown report."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))
ROOT = PROJECT / "eval"

from eval.experiments.threshold_sweep import sweep_min_relevance  # noqa: E402
from eval.runners.refund_rules import run_refund_rules_eval  # noqa: E402
from eval.runners.support_faq import run_support_faq_eval  # noqa: E402
from eval.runners.terms_retrieval import (  # noqa: E402
    run_terms_generation_eval,
    run_terms_retrieval_eval,
)
from eval.runners.url_rag import run_url_rag_eval  # noqa: E402
from eval.runners.wikivoyage import run_wikivoyage_eval  # noqa: E402

REPORTS_DIR = ROOT / "reports"
ARTIFACTS_DIR = ROOT / "artifacts"


def _write_report(payload: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = ARTIFACTS_DIR / f"baseline_{stamp}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_path = REPORTS_DIR / "EVAL_REPORT.md"
    s = payload["summary"]
    lines = [
        "# Travel Planner — Evaluation Report",
        "",
        f"_Generated: {payload['generated_at']}_",
        "",
        "## Status legend",
        "- **Passed** / **Failed** — automated eval result",
        "- **Requires API credentials** — set `EVAL_LIVE=1` and `GEMINI_API_KEY` for live embed/judge",
        "- **Requires human review** — complex policy interpretation",
        "",
        "## 1. Architecture (verified)",
        "Separate stacks: Terms FAISS+Gemini, Support FAQ rules+RAG, Wikivoyage TF-IDF, URL FAISS (optional), Refund rules engine.",
        "",
        "## 2. Terms / Policy RAG — retrieval (FakeEmbeddings CI)",
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
        "## 6. URL scrape RAG (optional)",
        f"- Pass rate: {s['url_rag']['pass_rate']}",
        f"- Used in production chat: **No** (`retrieve_from_url` not wired to UI chat)",
        "",
        "## 7. Refund rules engine",
        f"- Pass rate: {s['refund_rules']['pass_rate']}",
        "",
        "## 8. Threshold experiment (eval harness)",
        "See artifact JSON `experiments.min_relevance_sweep`.",
        "",
        "## 9. LLM-as-Judge",
        "**Not tested** in baseline (requires `EVAL_LIVE=1`). Prompt: `eval/evaluators/llm_judge.py`.",
        "",
        "## 10. Live Gemini embeddings",
        "**Not tested** in default baseline — FakeEmbeddings used. Run with `EVAL_LIVE=1` for real embed quality (future runner flag).",
        "",
        f"Full JSON artifact: `{json_path.relative_to(PROJECT)}`",
        "",
        "## Failure analysis",
        "Inspect `eval/artifacts/baseline_*.json` `details.*_rows` where `pass` is false.",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def main() -> int:
    terms_ret = run_terms_retrieval_eval()
    terms_gen = run_terms_generation_eval()
    support = run_support_faq_eval()
    wiki = run_wikivoyage_eval()
    url = run_url_rag_eval()
    refund = run_refund_rules_eval()
    sweep = sweep_min_relevance()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "terms_retrieval": terms_ret["summary"],
            "terms_generation": terms_gen["summary"],
            "support_faq": support["summary"],
            "wikivoyage": wiki["summary"],
            "url_rag": url["summary"],
            "refund_rules": refund["summary"],
        },
        "experiments": {"min_relevance_sweep": sweep},
        "details": {
            "terms_retrieval_rows": terms_ret["rows"],
            "terms_generation_rows": terms_gen["rows"],
            "support_faq_rows": support["rows"],
            "wikivoyage_rows": wiki["rows"],
            "url_rag_rows": url["rows"],
            "refund_rules_rows": refund["rows"],
        },
    }
    report_path = _write_report(payload)
    print(f"Wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
