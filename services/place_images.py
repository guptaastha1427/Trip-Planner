"""
Free place photos via Wikipedia / Wikimedia (no API key).

What: Thumbnail URLs for cities, airports, hotels, and itinerary POIs.
Why: Visual context for beginners without paid image APIs.
How: Cached Wikipedia pageimages search; English Wikipedia first.
"""

from typing import Any, Dict, List, Optional

import streamlit as st

from config import MAX_ITINERARY_PHOTO_STOPS
from services.http_client import get_json

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


@st.cache_data(ttl=86400, show_spinner=False)
def wikimedia_thumbnail(query: str, user_agent: str, *, thumb_size: int = 420) -> Optional[str]:
    """Return a thumbnail URL for the best-matching Wikipedia article, or None."""
    q = (query or "").strip()
    if not q or not user_agent:
        return None
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": q,
        "gsrlimit": 1,
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": thumb_size,
        "format": "json",
    }
    try:
        data = get_json(WIKIPEDIA_API, user_agent, params=params)
    except Exception:
        return None
    pages = (data.get("query") or {}).get("pages") or {}
    for page in pages.values():
        thumb = (page.get("thumbnail") or {}).get("source")
        if thumb and str(thumb).startswith("https://"):
            return str(thumb)
    return None


@st.cache_data(ttl=86400, show_spinner=False)
def wikimedia_thumbnail_by_title(title: str, user_agent: str, *, thumb_size: int = 420) -> Optional[str]:
    """Direct pageimages lookup when we already have an article title."""
    t = (title or "").strip()
    if not t or not user_agent:
        return None
    params = {
        "action": "query",
        "titles": t,
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": thumb_size,
        "format": "json",
    }
    try:
        data = get_json(WIKIPEDIA_API, user_agent, params=params)
    except Exception:
        return None
    pages = (data.get("query") or {}).get("pages") or {}
    for page in pages.values():
        if page.get("missing"):
            continue
        thumb = (page.get("thumbnail") or {}).get("source")
        if thumb and str(thumb).startswith("https://"):
            return str(thumb)
    return None


def _query_variants(name: str, city_label: str, extra_context: str = "") -> List[str]:
    city = (city_label or "").split(",")[0].strip()
    name = (name or "").strip()
    if not name:
        return [city] if city else []
    variants = [
        f"{name} {city}",
        name,
        f"{city} {name}",
        f"{name} landmark {city}",
        f"{name} tourism",
    ]
    if "india" in (city_label or "").lower():
        variants.append(f"{name} India")
    if extra_context:
        variants.append(f"{name} {extra_context} {city}".strip())
    short = name.split("(")[0].strip()
    if short and short != name:
        variants.append(f"{short} {city}")
    words = name.split()
    if len(words) > 4:
        variants.append(" ".join(words[:3]) + f" {city}")
    seen: set = set()
    out: List[str] = []
    for v in variants:
        v = v.strip()
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out


def photo_for_place(
    name: str,
    city_label: str,
    user_agent: str,
    *,
    extra_context: str = "",
    aggressive: bool = False,
) -> Optional[str]:
    """Try place + city, then broader Wikipedia search queries."""
    for q in _query_variants(name, city_label, extra_context):
        url = wikimedia_thumbnail(q, user_agent)
        if url:
            return url
    if aggressive:
        for q in _query_variants(name, city_label, extra_context):
            url = wikimedia_thumbnail_by_title(q, user_agent)
            if url:
                return url
        city = (city_label or "").split(",")[0].strip()
        if city:
            url = wikimedia_thumbnail(city, user_agent)
            if url:
                return url
    return None


_BLOCKS = ("morning", "afternoon", "evening")


def _attach_photo_to_item(
    item: Dict[str, Any],
    city_label: str,
    user_agent: str,
    *,
    aggressive: bool,
) -> None:
    if item.get("image_url"):
        return
    name = item.get("name") or ""
    extra = item.get("category") or item.get("why") or ""
    url = photo_for_place(
        name,
        city_label,
        user_agent,
        extra_context=str(extra)[:80],
        aggressive=aggressive,
    )
    if url:
        item["image_url"] = url


def enrich_itinerary_with_photos(
    itinerary: Dict[str, Any],
    city_label: str,
    user_agent: str,
    *,
    max_stops: int = MAX_ITINERARY_PHOTO_STOPS,
) -> Dict[str, Any]:
    """Attach Wikipedia thumbnails (capped per run for responsiveness)."""
    if not itinerary or not user_agent:
        return itinerary
    count = 0
    for day in itinerary.get("days", []):
        for block in _BLOCKS:
            for item in day.get(block, []):
                if count >= max_stops:
                    return itinerary
                if item.get("image_url"):
                    continue
                _attach_photo_to_item(item, city_label, user_agent, aggressive=False)
                count += 1
    return itinerary


def _maybe_photo(entry: Optional[Dict[str, Any]], city_label: str, user_agent: str) -> None:
    if not entry or entry.get("image_url"):
        return
    label = entry.get("label") or entry.get("name") or ""
    url = photo_for_place(label, city_label, user_agent, aggressive=True)
    if url:
        entry["image_url"] = url


def enrich_travel_hints_photos(
    hints: Dict[str, Any],
    user_agent: str,
) -> Dict[str, Any]:
    """Second pass for airports, hotels, and endpoints missing thumbnails."""
    if not hints or not user_agent:
        return hints
    city_label = hints.get("city_label") or ""
    _maybe_photo(hints.get("destination"), city_label, user_agent)
    _maybe_photo(hints.get("source"), city_label, user_agent)
    for ap in (hints.get("airports") or [])[:2]:
        if not ap.get("image_url"):
            ap["image_url"] = photo_for_place(
                ap.get("name", ""),
                city_label,
                user_agent,
                aggressive=False,
            )
    for ht in (hints.get("budget_hotels") or hints.get("hotels") or [])[:3]:
        if not ht.get("image_url"):
            ht["image_url"] = photo_for_place(
                ht.get("name", ""),
                city_label,
                user_agent,
                aggressive=False,
            )
    return hints
