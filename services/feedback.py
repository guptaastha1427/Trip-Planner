"""
User feedback on POIs (upvote/downvote) stored in JSONL.

What: Append-only log of votes; aggregated boost scores per city + poi_id.
Why: Capstone requires learning from feedback to re-rank future POI search.
How: Read all events, sum boosts (+0.25 up, -0.35 down), scoped by city_key.
"""

import json
import time
from pathlib import Path
from typing import Dict, List

from config import DOWNVOTE_BOOST, FEEDBACK_PATH, UPVOTE_BOOST


def ensure_feedback_file() -> None:
    """Create data dir and empty JSONL if missing."""
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_PATH.exists():
        FEEDBACK_PATH.write_text("", encoding="utf-8")


def append_feedback(city_key: str, poi_id: str, vote: str) -> None:
    """
    Record one vote. vote must be 'up' or 'down'.
    """
    if vote not in ("up", "down"):
        raise ValueError("vote must be 'up' or 'down'")
    ensure_feedback_file()
    event = {
        "ts": time.time(),
        "city_key": city_key.lower().strip(),
        "poi_id": poi_id,
        "vote": vote,
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def load_feedback_events() -> List[dict]:
    """Load all feedback lines; skip malformed rows."""
    ensure_feedback_file()
    events: List[dict] = []
    for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def feedback_boost_map(city_key: str) -> Dict[str, float]:
    """
    Sum boosts for each poi_id in this city only (same POI id in another city is separate).
    """
    key = city_key.lower().strip()
    boosts: Dict[str, float] = {}
    for ev in load_feedback_events():
        if ev.get("city_key") != key:
            continue
        pid = ev.get("poi_id")
        if not pid:
            continue
        delta = UPVOTE_BOOST if ev.get("vote") == "up" else DOWNVOTE_BOOST
        boosts[pid] = boosts.get(pid, 0.0) + delta
    return boosts


def feedback_stats(city_key: str) -> Dict[str, Dict[str, int]]:
    """Optional UI: count ups/downs per poi_id in a city."""
    key = city_key.lower().strip()
    stats: Dict[str, Dict[str, int]] = {}
    for ev in load_feedback_events():
        if ev.get("city_key") != key:
            continue
        pid = ev.get("poi_id", "")
        stats.setdefault(pid, {"up": 0, "down": 0})
        if ev.get("vote") == "up":
            stats[pid]["up"] += 1
        elif ev.get("vote") == "down":
            stats[pid]["down"] += 1
    return stats
