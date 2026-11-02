"""Load evaluation datasets (JSONL)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List

EVAL_ROOT = Path(__file__).resolve().parents[1]
DATASETS_DIR = EVAL_ROOT / "datasets"


def load_jsonl(name: str) -> List[Dict[str, Any]]:
    path = DATASETS_DIR / name
    rows: List[Dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rows.append(json.loads(line))
    return rows


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                yield json.loads(line)
