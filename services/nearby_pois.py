"""
Nearby POI suggestions for itinerary stops.

What: Rank catalog POIs by distance from a stop for horizontal “alternatives” UI.
Why: Users should see famous/nearby options without replanning the whole trip.
How: Haversine on tool_state catalog; mixed categories (not all parks/parking).
"""

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from services.poi_search import _interest_bucket


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _category_label(poi: dict) -> str:
    cat = (poi.get("category") or "place").replace("_", " ")
    if "=" in cat:
        cat = cat.split("=", 1)[-1]
    return cat.title()[:28]


def _is_low_value_nearby(poi: dict) -> bool:
    """Drop parking lots and name-only 'park' spam from swap suggestions."""
    cat = (poi.get("category") or "").lower()
    name = (poi.get("name") or "").lower().strip()
    if "parking" in cat or cat.endswith("=parking"):
        return True
    if name in ("park", "parking", "car park"):
        return True
    if "parking" in name and len(name) < 40:
        return True
    # OSM typo / generic "Park N" parking structures
    if name.startswith("park") and "parking" in cat:
        return True
    return False


def _fame_score(poi: dict) -> float:
    try:
        return float(poi.get("score", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _pick_diverse_nearby(candidates: List[dict], limit: int) -> List[dict]:
    """Mix landmark, culture, food, outdoors, etc. — nearest per bucket first."""
    if len(candidates) <= limit:
        return candidates

    buckets: Dict[str, List[dict]] = defaultdict(list)
    for p in candidates:
        buckets[_interest_bucket(p)].append(p)

    for lst in buckets.values():
        lst.sort(
            key=lambda x: (
                x.get("distance_km", 99),
                -_fame_score(x),
            )
        )

    order = ["landmark", "culture", "food", "outdoors", "shopping", "other", "stay"]
    picked: List[dict] = []
    picked_ids: Set[str] = set()
    round_i = 0
    max_rounds = limit * 2

    while len(picked) < limit and round_i < max_rounds:
        added = False
        for key in order:
            lst = buckets.get(key, [])
            if round_i >= len(lst):
                continue
            p = lst[round_i]
            pid = str(p.get("poi_id", ""))
            if pid in picked_ids:
                continue
            picked.append(p)
            picked_ids.add(pid)
            added = True
            if len(picked) >= limit:
                break
        if not added:
            break
        round_i += 1

    for p in candidates:
        pid = str(p.get("poi_id", ""))
        if pid in picked_ids:
            continue
        picked.append(p)
        picked_ids.add(pid)
        if len(picked) >= limit:
            break

    picked.sort(key=lambda x: float(x.get("distance_km", 99)))
    return picked[:limit]


def nearby_alternatives(
    catalog: Dict[str, dict],
    lat: Optional[float],
    lon: Optional[float],
    exclude_ids: Optional[Set[str]] = None,
    *,
    radius_km: float = 4.0,
    limit: int = 10,
) -> List[dict]:
    """POIs near (lat, lon): mixed types, nearest-first within picks."""
    if lat is None or lon is None:
        return []
    exclude = exclude_ids or set()
    out: List[dict] = []

    for poi in catalog.values():
        pid = str(poi.get("poi_id", ""))
        if not pid or pid in exclude:
            continue
        if _is_low_value_nearby(poi):
            continue
        plat = poi.get("lat")
        plon = poi.get("lon")
        if plat is None or plon is None:
            continue
        dist = haversine_km(float(lat), float(lon), float(plat), float(plon))
        if dist > radius_km:
            continue
        row = dict(poi)
        row["distance_km"] = round(dist, 1)
        row["category_label"] = _category_label(poi)
        out.append(row)

    out.sort(key=lambda p: (p.get("distance_km", 99), -_fame_score(p)))
    diverse = _pick_diverse_nearby(out, limit)
    return diverse
