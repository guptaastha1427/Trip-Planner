"""Ensure repo root is importable when running pytest from subfolders."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] #root of the project.
if str(ROOT) not in sys.path: #if the root of the project is not in the system path, add it to the system path.
    sys.path.insert(0, str(ROOT))
