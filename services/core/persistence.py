"""
Load/save app_state.json for itinerary persistence across refreshes.

What: Single JSON file in data/ holding last itinerary and form defaults.
Why: Capstone requires persistence so users don't lose work on refresh.
How: Merge updates; Streamlit session_state syncs with disk on changes.
"""

import json
from typing import Any, Dict

from config import APP_STATE_PATH, DATA_DIR


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_app_state() -> Dict[str, Any]:
    ensure_data_dir()
    if not APP_STATE_PATH.exists():
        return {}
    try:
        return json.loads(APP_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_app_state(state: Dict[str, Any]) -> None:
    ensure_data_dir()
    APP_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
