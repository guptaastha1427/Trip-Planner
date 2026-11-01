"""
Validate user inputs and AI-generated itinerary JSON.

What: Guards before agent calls and after model output.
Why: Capstone requires POI ids must exist in tool_state only.
How: JSON extract + schema checks + single-day refinement diff.
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

BLOCKS = ("morning", "afternoon", "evening")


def validate_trip_inputs(
    destination: str,
    trip_days: int,
    pace: str,
    interests: str,
) -> Tuple[bool, str]:
    """Basic UI validation before calling OpenAI."""
    if not destination or not destination.strip():
        return False, "Please enter a destination city."
    if trip_days < 1 or trip_days > 14:
        return False, "Trip length should be between 1 and 14 days."
    if pace not in ("relaxed", "moderate", "packed"):
        return False, "Schedule must be relaxed, moderate, or packed."
    if not interests or not interests.strip():
        return False, "Please enter at least one interest (comma-separated)."
    return True, ""


def extract_json(raw: str) -> Dict[str, Any]:
    """
    Parse itinerary JSON from model text (may include markdown fences).
    Raises ValueError with a beginner-friendly message.
    """
    if not raw or not str(raw).strip():
        raise ValueError("Model returned empty output.")

    text = str(raw).strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()

    # Sometimes the model wraps extra prose; find first { ... }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output.")
    text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc


def validate_itinerary_structure(itin: Dict[str, Any], expected_days: Optional[int] = None) -> None:
    """Ensure days/morning/afternoon/evening blocks exist."""
    if "days" not in itin or not isinstance(itin["days"], list):
        raise ValueError("Itinerary must contain a 'days' list.")
    if expected_days is not None and len(itin["days"]) != expected_days:
        raise ValueError(f"Expected {expected_days} days, got {len(itin['days'])}.")
    for i, day in enumerate(itin["days"]):
        if day.get("day") != i + 1:
            raise ValueError(f"Day index mismatch at position {i}.")
        for block in BLOCKS:
            if block not in day or not isinstance(day[block], list):
                raise ValueError(f"Day {i+1} missing block '{block}'.")


def validate_itinerary_poi_ids(itin: Dict[str, Any], allowed_pois: Dict[str, Any]) -> None:
    """Capstone example: every poi_id must exist in tool-returned POIs."""
    valid_ids: Set[str] = set(allowed_pois.keys())
    for day in itin["days"]:
        for block in BLOCKS:
            for item in day[block]:
                pid = item.get("poi_id")
                if pid not in valid_ids:
                    raise ValueError(f"Invalid poi_id: {pid}")


def itinerary_poi_id_set(itin: Dict[str, Any]) -> Set[str]:
    ids: Set[str] = set()
    for day in itin.get("days", []):
        for block in BLOCKS:
            for item in day.get(block, []):
                pid = item.get("poi_id")
                if pid:
                    ids.add(str(pid))
    return ids


def find_duplicate_poi_ids(itin: Dict[str, Any]) -> List[str]:
    """poi_id values that appear more than once across the full trip."""
    seen: Set[str] = set()
    duplicates: List[str] = []
    for day in itin.get("days", []):
        for block in BLOCKS:
            for item in day.get(block, []):
                pid = item.get("poi_id")
                if not pid:
                    continue
                pid_s = str(pid)
                if pid_s in seen and pid_s not in duplicates:
                    duplicates.append(pid_s)
                seen.add(pid_s)
    return duplicates


def validate_itinerary_unique_pois(itin: Dict[str, Any]) -> None:
    """Each poi_id may appear at most once in the itinerary."""
    dups = find_duplicate_poi_ids(itin)
    if dups:
        sample = ", ".join(dups[:5])
        raise ValueError(
            f"Duplicate places in itinerary (visit each poi_id only once): {sample}"
        )


def dedupe_itinerary_pois(itin: Dict[str, Any]) -> tuple[Dict[str, Any], int]:
    """Drop later repeats of the same poi_id (keeps first visit). Returns (itin, removed_count)."""
    seen: Set[str] = set()
    removed = 0
    for day in itin.get("days", []):
        for block in BLOCKS:
            kept: List[dict] = []
            for item in day.get(block, []):
                pid = item.get("poi_id")
                if pid:
                    pid_s = str(pid)
                    if pid_s in seen:
                        removed += 1
                        continue
                    seen.add(pid_s)
                kept.append(item)
            day[block] = kept
    return itin, removed


def enrich_itinerary_from_pois(itin: Dict[str, Any], allowed_pois: Dict[str, Any]) -> Dict[str, Any]:
    """Fill name/category/lat/lon from POI catalog when missing; remove duplicate stops."""
    for day in itin["days"]:
        for block in BLOCKS:
            for item in day[block]:
                pid = item.get("poi_id")
                poi = allowed_pois.get(pid)
                if poi:
                    item["name"] = poi.get("name") or item.get("name")
                    item.setdefault("category", poi["category"])
                    item.setdefault("lat", poi["lat"])
                    item.setdefault("lon", poi["lon"])
    dedupe_itinerary_pois(itin)
    return itin


def verify_single_day_unchanged(
    before: Dict[str, Any],
    after: Dict[str, Any],
    target_day: int,
) -> None:
    """
    After single-day regeneration, all days except target_day must match exactly.
    """
    for day in before["days"]:
        num = day["day"]
        after_day = next((d for d in after["days"] if d["day"] == num), None)
        if after_day is None:
            raise ValueError(f"Missing day {num} in refined itinerary.")
        if num == target_day:
            continue
        if json.dumps(day, sort_keys=True) != json.dumps(after_day, sort_keys=True):
            raise ValueError(f"Day {num} changed but should have stayed identical.")
