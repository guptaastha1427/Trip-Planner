"""
search_pois tool: geocode + Overpass POI query with interest tag mapping.

What: Finds museums, restaurants, parks, etc. near a destination.
Why: The agent must only recommend places that exist in OpenStreetMap data.
How: Build Overpass QL with regex on tags; rank with base score + feedback boosts.
"""

import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from config import OVERPASS_URL
from services.feedback import feedback_boost_map
from services.geocoding import geocode_city
from services.http_client import post_text

# Capstone-specified interest → OSM tag mapping (regex in Overpass)
_QUERY_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "go",
        "want",
        "i",
        "we",
        "my",
        "add",
        "visit",
        "include",
        "please",
        "day",
        "trip",
        "more",
        "less",
    }
)


def _matches_query_text(name: str, query_text: str) -> bool:
    """Match POI names to natural-language refine requests (e.g. 'go to Bharat Mandapam')."""
    name_l = name.lower()
    q = query_text.lower().strip()
    if not q:
        return True
    if q in name_l:
        return True
    tokens = [t for t in re.split(r"\W+", q) if len(t) > 2 and t not in _QUERY_STOPWORDS]
    if not tokens:
        return True
    return any(tok in name_l for tok in tokens)


INTEREST_TO_TAGS: Dict[str, List[tuple]] = {
    "museums": [("tourism", "museum|gallery")],
    "food": [("amenity", "restaurant|cafe|fast_food|bar|pub")],
    "outdoors": [("leisure", "park|nature_reserve"), ("natural", "peak|beach")],
    "history": [("historic", ".*"), ("tourism", "attraction|artwork")],
    "shopping": [("shop", ".*")],
    "nightlife": [("amenity", "nightclub|bar|pub")],
    "family": [("tourism", "zoo|theme_park|aquarium"), ("leisure", "playground")],
}

# Normalize free-text interests from the UI/agent to keys above
INTEREST_ALIASES: Dict[str, str] = {
    "museum": "museums",
    "museums": "museums",
    "art": "museums",
    "food": "food",
    "dining": "food",
    "restaurants": "food",
    "outdoor": "outdoors",
    "outdoors": "outdoors",
    "nature": "outdoors",
    "parks": "outdoors",
    "history": "history",
    "historic": "history",
    "shopping": "shopping",
    "nightlife": "nightlife",
    "family": "family",
    "kids": "family",
}


def normalize_interests(interests: List[str]) -> List[str]:
    """Map user strings to canonical interest keys for tag lookup."""
    out: List[str] = []
    for raw in interests:
        key = INTEREST_ALIASES.get(raw.lower().strip(), raw.lower().strip())
        if key in INTEREST_TO_TAGS and key not in out:
            out.append(key)
    if not out:
        out = ["museums", "food", "outdoors"]
    return out


def _bbox_from_geocode(geo: Dict[str, Any], padding: float = 0.08) -> tuple:
    """Use Nominatim bounding box or a small box around center."""
    bb = geo.get("boundingbox")
    if bb and len(bb) == 4:
        south, north, west, east = map(float, bb)
        return south, west, north, east
    lat, lon = geo["lat"], geo["lon"]
    return lat - padding, lon - padding, lat + padding, lon + padding


def _build_overpass_query(
    south: float,
    west: float,
    north: float,
    east: float,
    interests: List[str],
    *,
    fast: bool = False,
) -> str:
    """
    Overpass QL: nodes/ways/relations with name in bbox, filtered by tag regex.
    """
    if fast:
        interests = interests[:5]

    tag_filters: List[str] = []
    for interest in interests:
        for key, pattern in INTEREST_TO_TAGS.get(interest, []):
            # Overpass regex: ~"pattern" on tag value
            tag_filters.append(f'["{key}"~"{pattern}"]')

    if not tag_filters:
        tag_filters.append('["tourism"]')

    # Union of tag conditions (any match)
    union_parts = []
    for tf in tag_filters:
        bbox = f"{south},{west},{north},{east}"
        union_parts.append(f'  node{tf}({bbox});')
        # Ways often map monuments; include for landmark-heavy tags even in fast mode.
        if not fast or any(
            k in tf for k in ('historic', 'museum', 'attraction', 'gallery', 'viewpoint')
        ):
            union_parts.append(f'  way{tf}({bbox});')

    body = "\n".join(union_parts)
    timeout = 15 if fast else 25
    return f"""
[out:json][timeout:{timeout}];
(
{body}
);
out center tags;
"""


def _build_landmarks_query(
    south: float,
    west: float,
    north: float,
    east: float,
) -> str:
    """Extra pass for famous / notable sights (attractions, museums, historic)."""
    bbox = f"{south},{west},{north},{east}"
    parts = [
        f'  node["tourism"~"attraction|museum|gallery|viewpoint|theme_park"]({bbox});',
        f'  way["tourism"~"attraction|museum|gallery|viewpoint|theme_park"]({bbox});',
        f'  node["historic"]({bbox});',
        f'  way["historic"]({bbox});',
        f'  node["wikidata"]({bbox});',
        f'  way["wikidata"]({bbox});',
    ]
    body = "\n".join(parts)
    return f"""
[out:json][timeout:20];
(
{body}
);
out center tags;
"""


def _osm_poi_id(element: dict) -> str:
    """Stable id string for itinerary validation (capstone example: osm_way_12345)."""
    osm_type = element.get("type", "node")
    osm_id = element.get("id")
    return f"osm_{osm_type}_{osm_id}"


def english_display_name(tags: dict) -> Optional[str]:
    """Prefer English labels so the UI stays readable for all users."""
    for key in ("name:en", "int_name", "official_name:en", "alt_name:en", "name"):
        val = tags.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return None


def _category_from_tags(tags: dict) -> str:
    """Human-readable category from OSM tags."""
    for key in ("tourism", "amenity", "leisure", "historic", "natural", "shop"):
        if key in tags:
            return f"{key}={tags[key]}"
    return "poi"


def _base_score(tags: dict, name: str) -> float:
    """Rank notable / famous OSM features above generic cafes and shops."""
    score = 1.0
    if name:
        score += 0.5
    tourism = str(tags.get("tourism") or "")
    if tourism in ("attraction", "museum", "gallery", "viewpoint", "theme_park", "zoo"):
        score += 2.5
    elif tourism:
        score += 0.4
    if tags.get("historic"):
        score += 2.0
    if tags.get("heritage"):
        score += 1.2
    if tags.get("amenity") in ("restaurant", "cafe"):
        score += 0.35
    if tags.get("wikidata"):
        score += 2.2
    if tags.get("wikipedia"):
        score += 2.0
    if tags.get("unesco") or tags.get("heritage:operator"):
        score += 1.5
    return score


def _interest_bucket(poi: dict) -> str:
    cat = (poi.get("category") or "").lower()
    if "museum" in cat or "gallery" in cat:
        return "culture"
    if "historic" in cat or "attraction" in cat or "monument" in cat:
        return "landmark"
    if "restaurant" in cat or "cafe" in cat or "food" in cat or "bar" in cat:
        return "food"
    if "park" in cat or "nature" in cat or "beach" in cat or "peak" in cat:
        return "outdoors"
    if "shop" in cat:
        return "shopping"
    if "hotel" in cat or "hostel" in cat:
        return "stay"
    return "other"


def _trim_diverse_pois(ranked: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Keep top scores but ensure mixed categories (not all museums)."""
    if len(ranked) <= limit:
        return ranked
    buckets: Dict[str, List[dict]] = defaultdict(list)
    for p in ranked:
        buckets[_interest_bucket(p)].append(p)
    order = ["landmark", "culture", "outdoors", "food", "shopping", "other", "stay"]
    picked: List[dict] = []
    picked_ids: Set[str] = set()
    per_bucket = max(2, limit // 5)
    for key in order:
        for p in buckets.get(key, [])[:per_bucket]:
            pid = p.get("poi_id")
            if pid in picked_ids:
                continue
            picked.append(p)
            picked_ids.add(pid)
            if len(picked) >= limit:
                return picked
    for p in ranked:
        pid = p.get("poi_id")
        if pid in picked_ids:
            continue
        picked.append(p)
        picked_ids.add(pid)
        if len(picked) >= limit:
            break
    return picked


def _elements_to_pois(
    elements: List[dict],
    boosts: Dict[str, float],
    query_text: Optional[str],
) -> Dict[str, Dict[str, Any]]:
    pois: Dict[str, Dict[str, Any]] = {}
    for el in elements:
        tags = el.get("tags") or {}
        name = english_display_name(tags)
        if not name:
            continue
        if query_text and not _matches_query_text(name, query_text):
            continue
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            center = el.get("center") or {}
            lat = center.get("lat")
            lon = center.get("lon")
        if lat is None or lon is None:
            continue
        poi_id = _osm_poi_id(el)
        base = _base_score(tags, name)
        boost = boosts.get(poi_id, 0.0)
        pois[poi_id] = {
            "poi_id": poi_id,
            "name": name,
            "category": _category_from_tags(tags),
            "lat": float(lat),
            "lon": float(lon),
            "url": f"https://www.openstreetmap.org/{el.get('type', 'node')}/{el.get('id')}",
            "_base_score": base,
            "_score": base + boost,
        }
    return pois


@st.cache_data(ttl=3600)
def _fetch_overpass_cached(query: str, user_agent: str) -> str:
    """Cache raw Overpass JSON text (keyed by query + user agent)."""
    return post_text(OVERPASS_URL, user_agent, data=query)


def search_pois(
    city: str,
    interests: List[str],
    user_agent: str,
    limit: int = 30,
    query_text: Optional[str] = None,
    *,
    fast: bool = False,
) -> Dict[str, Any]:
    """
    Main tool entry: geocode city, query Overpass, return POIs dict keyed by poi_id.

    Also returns city_meta for the agent and errors list for UI.
    """
    geo = geocode_city(city, user_agent)
    if not geo:
        return {
            "ok": False,
            "error": f"Geocoding found no results for '{city}'. Try a more specific name.",
            "pois": {},
            "city_meta": None,
        }

    norm_interests = normalize_interests(interests)
    south, west, north, east = _bbox_from_geocode(geo)
    overpass_q = _build_overpass_query(
        south, west, north, east, norm_interests, fast=fast
    )

    boosts = feedback_boost_map(geo["city_key"])
    elements: List[dict] = []
    try:
        raw = _fetch_overpass_cached(overpass_q, user_agent)
        elements.extend(json.loads(raw).get("elements", []))
        landmark_q = _build_landmarks_query(south, west, north, east)
        raw_lm = _fetch_overpass_cached(landmark_q, user_agent)
        elements.extend(json.loads(raw_lm).get("elements", []))
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"Overpass API failed: {exc}",
            "pois": {},
            "city_meta": geo,
        }

    pois = _elements_to_pois(elements, boosts, query_text)
    ranked = sorted(pois.values(), key=lambda p: p["_score"], reverse=True)
    trimmed = _trim_diverse_pois(ranked, max(1, min(limit, 80)))
    pois_out = {p["poi_id"]: p for p in trimmed}

    if not pois_out:
        return {
            "ok": False,
            "error": "No POIs matched your interests in this area. Try broader interests or another city.",
            "pois": {},
            "city_meta": geo,
        }

    return {
        "ok": True,
        "pois": pois_out,
        "city_meta": geo,
        "interests_used": norm_interests,
    }
