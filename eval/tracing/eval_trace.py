"""JSONL evaluation trace writer (no secrets)."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, Optional

EVAL_ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = EVAL_ROOT / "traces"

_SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
    re.compile(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*\S+"),
)


def redact(text: str) -> str:
    out = text or ""
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def write_trace(record: Dict[str, Any], *, run_id: Optional[str] = None) -> Path:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    rid = run_id or time.strftime("%Y%m%d-%H%M%S")
    path = TRACES_DIR / f"eval_{rid}.jsonl"
    safe = json.loads(json.dumps(record, default=str))
    if "query" in safe:
        safe["query"] = redact(str(safe["query"]))
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(safe, ensure_ascii=False) + "\n")
    return path
