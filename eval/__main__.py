"""Run baseline evaluation: python -m eval (from repo root, app venv active)."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from eval.run_baseline import main

if __name__ == "__main__":
    raise SystemExit(main())
