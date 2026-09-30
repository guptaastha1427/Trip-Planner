"""
Geocode city names via Nominatim (OpenStreetMap).

What: Turns "Santa Fe, NM" into latitude, longitude, and display name.
Why: Overpass POI queries need a bounding box or center point around the city.
How: Cached Streamlit function calls Nominatim search with limit=1.
"""

from typing import Any, Dict, Optional

import streamlit as st

from config import NOMINATIM_URL
from services.http_client import get_json


@st.cache_data(ttl=3600)
def geocode_city(city: str, user_agent: str) -> Optional[Dict[str, Any]]:
    """
    Return geocode metadata or None if Nominatim finds no match.

    Example keys: lat, lon, display_name, boundingbox (for Overpass area).
    """
    city = (city or "").strip()
    if not city:
        return None

    params = {
        "q": city,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    try:
        results = get_json(
            NOMINATIM_URL, user_agent, params=params, use_nominatim_limit=True
        )
    except Exception:
        return None

    if not results:
        return None

    hit = results[0]
    return {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "display_name": hit.get("display_name", city),
        "boundingbox": hit.get("boundingbox"),  # [south, north, west, east] as strings
        "city_key": city.lower().strip(),
    }
