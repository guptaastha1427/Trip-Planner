"""
Apply user refinement requests to an existing itinerary.

What: Programmatic POI swap/add when the model returns unchanged JSON.
Why: Refine must visibly update stops using OSM-backed poi_id values.
How: Match request text to catalog, replace or append a day/block slot.
"""

import copy
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from services.geocoding import geocode_city
from services.poi_search import _matches_query_text
from services.validation import BLOCKS, enrich_itinerary_from_pois, itinerary_poi_id_set


def itinerary_poi_sequence(itin: Dict[str, Any]) -> List[str]:
    seq: List[str] = []
    for day in itin.get("days", []):
        for block in BLOCKS:
            for item in day.get(block, []):
                seq.append(str(item.get("poi_id", "")))
    return seq


def itineraries_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return itinerary_poi_sequence(a) == itinerary_poi_sequence(b)


def _score_poi_name(name: str, phrase: str) -> int:
    name_l = name.lower()
    tokens = [t for t in re.split(r"\W+", phrase.lower()) if len(t) > 2]
    if not tokens:
        return 0
    return sum(1 for t in tokens if t in name_l)


def _quoted_phrase(user_request: str) -> str:
    m = re.search(r'"([^"]+)"|\'([^\']+)\'', user_request)
    if m:
        return (m.group(1) or m.group(2) or "").strip()
    return ""


def _search_phrases(user_request: str, phrase: str) -> List[str]:
    out: List[str] = []
    for p in (_quoted_phrase(user_request), phrase, user_request):
        p = (p or "").strip()
        if p and p not in out:
            out.append(p)
    return out


def _place_tokens(place: str) -> List[str]:
    return [t for t in re.split(r"\W+", (place or "").lower()) if len(t) > 2]


def _matches_place_name(poi_name: str, place: str) -> bool:
    tokens = _place_tokens(place)
    if len(tokens) >= 2:
        name_l = (poi_name or "").lower()
        return all(t in name_l for t in tokens)
    return _matches_query_text(poi_name, place)


def upsert_geocoded_poi(
    pois: Dict[str, dict],
    place: str,
    destination: str,
    user_agent: str,
) -> Optional[dict]:
    """Resolve a named place via Nominatim and add it to the POI catalog."""
    place = (place or "").strip()
    if not place or not (user_agent or "").strip():
        return None
    dest = (destination or "").strip()
    geo = None
    if dest:
        geo = geocode_city(f"{place}, {dest}", user_agent)
    if not geo:
        geo = geocode_city(place, user_agent)
    if not geo:
        return None
    lat = float(geo["lat"])
    lon = float(geo["lon"])
    pid = f"osm_refine_{round(lat, 5)}_{round(lon, 5)}"
    name = (geo.get("display_name") or place).split(",")[0].strip()
    pois[pid] = {
        "poi_id": pid,
        "name": name,
        "category": "tourism=attraction",
        "lat": lat,
        "lon": lon,
        "url": "",
        "_score": 999.0,
    }
    return pois[pid]


def find_poi_for_request(
    pois: Dict[str, dict],
    phrase: str,
    exclude_ids: Optional[set] = None,
) -> Optional[dict]:
    if not pois:
        return None
    phrase = (phrase or "").strip()
    exclude = exclude_ids or set()
    for poi in pois.values():
        if str(poi.get("poi_id", "")) in exclude:
            continue
        if phrase and _matches_place_name(poi.get("name", ""), phrase):
            return poi
    ranked = sorted(
        [
            p
            for p in pois.values()
            if str(p.get("poi_id", "")) not in exclude
        ],
        key=lambda p: (_score_poi_name(p.get("name", ""), phrase), p.get("_score", 0)),
        reverse=True,
    )
    if ranked:
        best = ranked[0]
        tokens = _place_tokens(phrase)
        if len(tokens) >= 2 and all(t in best.get("name", "").lower() for t in tokens):
            return best
        if len(tokens) <= 1 and _score_poi_name(best.get("name", ""), phrase) > 0:
            return best
    return None


_REWRITE_HINTS = (
    "replan",
    "redo",
    "from scratch",
    "entire trip",
    "whole trip",
    "change everything",
    "new itinerary",
)


def extract_place_phrase(user_request: str) -> str:
    """Place name from requests like 'add Bharat Mandapam on day 2 afternoon'."""
    req = user_request.strip()
    quoted = _quoted_phrase(req)
    if quoted:
        return quoted
    m = re.match(
        r"^(?:please\s+)?(?:add|include|visit|go to)\s+(.+)$",
        req,
        re.I,
    )
    if m:
        rest = m.group(1).strip()
        rest = re.sub(r"\s+on\s+day\s+\d+.*$", "", rest, flags=re.I)
        rest = re.sub(
            r"\s+(?:in\s+the\s+)?(morning|afternoon|evening)\b.*$",
            "",
            rest,
            flags=re.I,
        )
        return rest.strip()
    return ""


def is_add_only_request(user_request: str) -> bool:
    req = user_request.lower().strip()
    if any(h in req for h in _REWRITE_HINTS):
        return False
    if re.search(r"\b(remove|delete|replan|redo|swap entire)\b", req):
        return False
    return bool(
        re.search(r"^\s*(?:please\s+)?(?:add|include)\b", req)
        or re.search(r"\b(?:add|include)\s+\w", req)
    )


def is_surgical_refine_request(user_request: str) -> bool:
    """Single-place add/replace — do not rewrite the whole trip with the model."""
    req = user_request.lower().strip()
    if any(h in req for h in _REWRITE_HINTS):
        return False
    if is_add_only_request(user_request):
        return True
    if re.search(r"\b(replace|swap|instead of)\b", req) and re.search(
        r"day\s*\d+", req
    ):
        return True
    return False


def is_minimal_add_delta(before: Dict[str, Any], after: Dict[str, Any]) -> bool:
    """True when `after` is `before` plus exactly one new stop."""
    old = itinerary_poi_sequence(before)
    new = itinerary_poi_sequence(after)
    if len(new) != len(old) + 1:
        return False
    for i in range(len(new)):
        if new[:i] + new[i + 1 :] == old:
            return True
    return False


def _best_add_slot(days: List[dict], num_days: int) -> Tuple[int, str]:
    best_day, best_block, best_count = 0, "afternoon", 10_000
    for day_idx in range(num_days):
        day = days[day_idx]
        for block in BLOCKS:
            count = len(day.get(block, []))
            if count < best_count:
                best_day, best_block, best_count = day_idx, block, count
    return best_day, best_block


def _pick_slot(
    user_request: str, num_days: int, days: Optional[List[dict]] = None
) -> Tuple[int, str]:
    req_l = user_request.lower()
    m = re.search(r"day\s*(\d+)", req_l)
    day_idx = 0
    if m:
        day_idx = max(0, min(int(m.group(1)) - 1, num_days - 1))
    block = "afternoon"
    if "morning" in req_l:
        block = "morning"
    elif "evening" in req_l:
        block = "evening"
    if not m and is_add_only_request(user_request) and days:
        return _best_add_slot(days, num_days)
    return day_idx, block


def apply_programmatic_refine(
    itinerary: Dict[str, Any],
    pois: Dict[str, dict],
    user_request: str,
    phrase: str,
    target_day: Optional[int] = None,
    destination: str = "",
    user_agent: str = "",
) -> Dict[str, Any]:
    """Swap or add a catalog POI so the itinerary actually changes."""
    itin = copy.deepcopy(itinerary)
    place_hint = extract_place_phrase(user_request)
    search_order: List[str] = []
    if place_hint:
        search_order.append(place_hint)
    for p in _search_phrases(user_request, phrase):
        if p not in search_order:
            search_order.append(p)
    used_ids = itinerary_poi_id_set(itin)
    poi = None
    for p in search_order:
        poi = find_poi_for_request(pois, p, exclude_ids=used_ids)
        if poi:
            break
    if not poi and place_hint:
        poi = upsert_geocoded_poi(pois, place_hint, destination, user_agent)
    if not poi and phrase:
        poi = upsert_geocoded_poi(pois, phrase, destination, user_agent)
    if not poi:
        return itin

    days = itin.get("days", [])
    if not days:
        return itin

    new_item = {
        "poi_id": poi["poi_id"],
        "name": poi["name"],
        "why": f"Updated for your request: {user_request[:160]}",
        "category": poi.get("category", ""),
        "lat": poi.get("lat"),
        "lon": poi.get("lon"),
    }
    new_pid = str(new_item["poi_id"])
    req_l = user_request.lower()
    add_words = ("add", "include", "visit", "also", "another", "extra")

    def _block_ids(day_obj: dict, blk: str) -> List[str]:
        return [str(a.get("poi_id", "")) for a in day_obj.get(blk, [])]

    slots: List[Tuple[int, str]] = []
    if target_day is not None and 1 <= target_day <= len(days):
        primary_day = target_day - 1
        _, primary_block = _pick_slot(user_request, len(days), days)
    else:
        primary_day, primary_block = _pick_slot(user_request, len(days), days)
    slots.append((primary_day, primary_block))
    for blk in BLOCKS:
        if blk != primary_block:
            slots.append((primary_day, blk))
    for d in range(len(days)):
        if d != primary_day:
            slots.append((d, "afternoon"))

    for day_idx, block in slots:
        day = days[day_idx]
        if block not in day:
            day[block] = []
        activities: List[dict] = list(day.get(block, []))
        ids = _block_ids(day, block)

        if new_pid in ids and not any(w in req_l for w in ("remove", "replace", "swap", "instead")):
            continue

        if any(w in req_l for w in add_words):
            if new_pid not in used_ids:
                activities.append(new_item)
                day[block] = activities
                itin = enrich_itinerary_from_pois(itin, pois)
                return itin
            continue

        if activities:
            replace_idx = 0
            for i, act in enumerate(activities):
                if _matches_query_text(act.get("name", ""), phrase) or _matches_query_text(
                    act.get("name", ""), user_request
                ):
                    replace_idx = i
                    break
            old_pid = str(activities[replace_idx].get("poi_id", ""))
            if new_pid != old_pid and new_pid in used_ids:
                continue
            activities[replace_idx] = new_item
        else:
            activities.append(new_item)

        day[block] = activities
        itin = enrich_itinerary_from_pois(itin, pois)
        if not itineraries_equal(itinerary, itin):
            return itin

    return itin


def try_surgical_refine(
    before: Dict[str, Any],
    pois: Dict[str, dict],
    user_request: str,
    phrase: str,
    target_day: Optional[int] = None,
    destination: str = "",
    user_agent: str = "",
) -> Optional[Dict[str, Any]]:
    """Add/replace one stop without calling the model."""
    if not is_surgical_refine_request(user_request):
        return None
    after = apply_programmatic_refine(
        before,
        pois,
        user_request,
        phrase,
        target_day=target_day,
        destination=destination,
        user_agent=user_agent,
    )
    if itineraries_equal(before, after):
        return None
    return after


def ensure_refinement_changed(
    before: Dict[str, Any],
    candidate: Optional[Dict[str, Any]],
    pois: Dict[str, dict],
    user_request: str,
    phrase: str,
    target_day: Optional[int] = None,
    destination: str = "",
    user_agent: str = "",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return changed itinerary or an error message."""
    if candidate and not itineraries_equal(before, candidate):
        if is_add_only_request(user_request) and not is_minimal_add_delta(
            before, candidate
        ):
            candidate = None
        else:
            return candidate, None

    forced = apply_programmatic_refine(
        before,
        pois,
        user_request,
        phrase,
        target_day=target_day,
        destination=destination,
        user_agent=user_agent,
    )
    if not itineraries_equal(before, forced):
        return forced, None

    if is_add_only_request(user_request):
        place = extract_place_phrase(user_request) or phrase
        return None, (
            f'Could not find "{place}" to add. Try the full name and optional slot, e.g. '
            '"add Bharat Mandapam on day 1 afternoon". '
            "The place must be reachable on your trip (same city/region as your destination)."
        )
    return None, (
        "Could not apply that change. Use a place name in your destination city, "
        'e.g. "add Museum of Goa on day 2 afternoon".'
    )
