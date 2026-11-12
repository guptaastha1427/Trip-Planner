#!/usr/bin/env python3
"""
Regenerate eval/reports/EVAL_REPORT.md from an existing artifact (no re-run).

  python3 -m eval.report
  python3 -m eval.report --artifact eval/artifacts/baseline_20261112T105743Z.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Sequence

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from eval.helpers.eval_report import write_eval_report  # noqa: E402

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


def _latest_baseline_json() -> Optional[Path]:
    candidates = sorted(ARTIFACTS_DIR.glob("baseline_*.json"), reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("pipeline") == "eval.run_pipeline":
            return path
    return candidates[0] if candidates else None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Write EVAL_REPORT.md from artifact JSON")
    p.add_argument(
        "--artifact",
        default="",
        help="Path to baseline_*.json (default: newest pipeline baseline in eval/artifacts/)",
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.artifact:
        json_path = Path(args.artifact)
        if not json_path.is_file():
            json_path = PROJECT / args.artifact
    else:
        json_path = _latest_baseline_json()
    if not json_path or not json_path.is_file():
        print("No artifact found. Run: python3 -m eval.run_pipeline --refresh-baseline --report", file=sys.stderr)
        return 1
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    md_path = write_eval_report(payload, project_root=PROJECT, artifact_path=json_path.resolve())
    print(f"Wrote {md_path} from {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
