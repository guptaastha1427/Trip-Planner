"""
Trip history stored inside data/app_state.json (capstone data/ layout).

What: List of past itineraries under the "trip_history" key in app_state.
Why: Capstone allows only app_state.json + feedback.jsonl in data/.
How: load/save via services.persistence; session cache for instant sidebar loads.
"""

import copy
import json
import time
import uuid
from typing import List, Optional

import streamlit as st

from services.persistence import load_app_state, save_app_state

__all__ = [
    "load_trip_history",
    "get_trip_history_cached",
    "save_trip_history",
    "list_trip_history_for_portal_user",
    "clear_trip_history_for_portal_user",
    "append_trip_record",
    "snapshot_history_entry",
    "find_history_entry",
    "history_button_label",
]


def _migrate_legacy_file() -> None:
    """One-time: move data/trip_history.json into app_state if it still exists."""
    from config import DATA_DIR

    legacy = DATA_DIR / "trip_history.json"
    if not legacy.is_file():
        return
    try:
        entries = json.loads(legacy.read_text(encoding="utf-8"))
        if isinstance(entries, list) and entries:
            state = load_app_state()
            state.setdefault("trip_history", [])
            state["trip_history"] = state["trip_history"] + entries
            if len(state["trip_history"]) > 30:
                state["trip_history"] = state["trip_history"][-30:]
            save_app_state(state)
        legacy.unlink()
    except (OSError, json.JSONDecodeError):
        pass


def load_trip_history() -> List[dict]:
    _migrate_legacy_file()
    state = load_app_state()
    history = state.get("trip_history")
    return history if isinstance(history, list) else []


def get_trip_history_cached() -> List[dict]:
    """In-memory list for sidebar — avoids re-reading disk every rerun."""
    if "trip_history_cache" not in st.session_state:
        st.session_state.trip_history_cache = load_trip_history()
    return st.session_state.trip_history_cache


def _trip_owner_id(entry: dict) -> str:
    from services.demo_users import DEFAULT_USER_ID

    owner = entry.get("portal_user_id")
    if isinstance(owner, str) and owner:
        return owner
    return DEFAULT_USER_ID


def list_trip_history_for_portal_user(portal_user_id: str) -> List[dict]:
    return [
        entry
        for entry in get_trip_history_cached()
        if _trip_owner_id(entry) == portal_user_id
    ]


def clear_trip_history_for_portal_user(portal_user_id: str, *, persist_disk: bool = True) -> None:
    kept = [
        entry
        for entry in get_trip_history_cached()
        if _trip_owner_id(entry) != portal_user_id
    ]
    save_trip_history(kept, persist_disk=persist_disk)


def save_trip_history(entries: List[dict], *, persist_disk: bool = True) -> None:
    st.session_state.trip_history_cache = entries
    if not persist_disk:
        return
    state = load_app_state()
    state["trip_history"] = entries
    save_app_state(state)


def append_trip_record(
    *,
    destination: str,
    origin: str = "",
    trip_days: int,
    pace: str,
    interests: str,
    constraints: str,
    itinerary: dict,
    tool_state: dict,
    portal_user_id: Optional[str] = None,
    persist_disk: bool = True,
) -> dict:
    if not portal_user_id:
        from services.portal_user_context import resolve_portal_user_id

        portal_user_id = resolve_portal_user_id()
    entry = {
        "id": str(uuid.uuid4())[:8],
        "created_at": time.strftime("%Y-%m-%d %H:%M"),
        "destination": destination,
        "origin": origin,
        "trip_days": trip_days,
        "pace": pace,
        "interests": interests,
        "constraints": constraints,
        "portal_user_id": portal_user_id,
        "itinerary": copy.deepcopy(itinerary),
        "tool_state": copy.deepcopy(tool_state),
    }
    history = get_trip_history_cached()
    history.append(entry)
    if len(history) > 30:
        history = history[-30:]
    save_trip_history(history, persist_disk=persist_disk)
    st.session_state.active_history_id = entry["id"]
    return entry


def snapshot_history_entry(
    entry_id: str,
    *,
    itinerary: dict,
    tool_state: dict,
    destination: str,
    origin: str,
    trip_days: int,
    pace: str,
    interests: str,
    constraints: str,
    persist_disk: bool = True,
) -> None:
    """Persist full enriched trip (hints, weather, photos) into history for instant reload."""
    if not entry_id:
        return
    history = get_trip_history_cached()
    updated = False
    for entry in history:
        if entry.get("id") != entry_id:
            continue
        entry["itinerary"] = copy.deepcopy(itinerary)
        entry["tool_state"] = copy.deepcopy(tool_state)
        entry["destination"] = destination
        entry["origin"] = origin
        entry["trip_days"] = trip_days
        entry["pace"] = pace
        entry["interests"] = interests
        entry["constraints"] = constraints
        updated = True
        break
    if updated:
        save_trip_history(history, persist_disk=persist_disk)


def find_history_entry(
    entry_id: str,
    portal_user_id: Optional[str] = None,
) -> Optional[dict]:
    for entry in get_trip_history_cached():
        if entry.get("id") != entry_id:
            continue
        if portal_user_id and _trip_owner_id(entry) != portal_user_id:
            continue
        return entry
    return None


def history_button_label(entry: dict) -> str:
    dest = entry.get("destination") or "Trip"
    days = entry.get("trip_days", "?")
    when = entry.get("created_at", "")
    return f"{dest} · {days}d · {when}"
