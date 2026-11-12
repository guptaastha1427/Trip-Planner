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
from eval.runners.wikivoyage import run_wikivoyage_eval  # noqa: E402
from eval.helpers.eval_report import write_legacy_baseline_report  # noqa: E402

ARTIFACTS_DIR = ROOT / "artifacts"


def _write_report(payload: dict, json_path: Path) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    return write_legacy_baseline_report(
        payload, project_root=PROJECT, artifact_path=json_path
    )


def main() -> int:
    terms_ret = run_terms_retrieval_eval()
    terms_gen = run_terms_generation_eval()
    support = run_support_faq_eval()
    wiki = run_wikivoyage_eval()
    refund = run_refund_rules_eval()
    sweep = sweep_min_relevance()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "terms_retrieval": terms_ret["summary"],
            "terms_generation": terms_gen["summary"],
            "support_faq": support["summary"],
            "wikivoyage": wiki["summary"],
            "refund_rules": refund["summary"],
        },
        "experiments": {"min_relevance_sweep": sweep},
        "details": {
            "terms_retrieval_rows": terms_ret["rows"],
            "terms_generation_rows": terms_gen["rows"],
            "support_faq_rows": support["rows"],
            "wikivoyage_rows": wiki["rows"],
            "refund_rules_rows": refund["rows"],
        },
    }
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = ARTIFACTS_DIR / f"baseline_{stamp}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path = _write_report(payload, json_path)
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")
    print(
        "Tip: for Ragas pipeline + synced report use "
        "python3 -m eval.run_pipeline --refresh-baseline --report"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
