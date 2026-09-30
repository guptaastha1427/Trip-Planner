"""
Short destination copy: about the place + best / avoid seasons.

What: Plain-language guide for the Travel tab.
Why: First-time visitors need context beyond POI lists.
How: Wikipedia intro + optional Gemini JSON; rule-based season hints as fallback.
"""

import re
from typing import Any, Dict, Optional

import streamlit as st
from google import genai
from google.genai import types

from config import (
    DEFAULT_MODEL,
    get_gemini_api_key,
    is_destination_guide_ai_enabled,
    is_wikivoyage_rag_enabled,
)
from services.agent import generate_content_with_fallback
from services.http_client import get_json
from services.validation import extract_json
from services.wikivoyage_rag import retrieve_guides

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


@st.cache_data(ttl=86400, show_spinner=False)
def _wikipedia_intro(query: str, user_agent: str) -> str:
    q = (query or "").strip()
    if not q:
        return ""
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": q,
        "srlimit": 1,
        "format": "json",
    }
    try:
        search = get_json(WIKIPEDIA_API, user_agent, params=search_params)
    except Exception:
        return ""
    hits = (search.get("query") or {}).get("search") or []
    if not hits:
        return ""
    title = hits[0].get("title") or q
    extract_params = {
        "action": "query",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "titles": title,
        "format": "json",
    }
    try:
        data = get_json(WIKIPEDIA_API, user_agent, params=extract_params)
    except Exception:
        return ""
    pages = (data.get("query") or {}).get("pages") or {}
    for page in pages.values():
        text = (page.get("extract") or "").strip()
        if text:
            return _trim_sentences(text, max_chars=520)
    return ""


def _trim_sentences(text: str, max_chars: int = 520) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if last > 120:
        return cut[: last + 1].strip()
    return cut.rstrip() + "…"


def _rule_seasons(lat: Optional[float], lon: Optional[float], city: str) -> Dict[str, str]:
    """Simple hemisphere / latitude bands when AI is unavailable."""
    name = city.split(",")[0].strip() or "this destination"
    if lat is None:
        return {
            "best_seasons": "Oct–Mar (cooler, drier months in many regions)",
            "avoid_seasons": "Peak monsoon / extreme heat weeks — check local forecasts",
            "season_tip": f"Cross-check dates with the Weather section for {name}.",
        }
    la = float(lat)
    if 6 <= la <= 37 and (lon is None or 68 <= float(lon) <= 97):
        return {
            "best_seasons": "Oct–Mar (pleasant weather across much of India)",
            "avoid_seasons": "Jun–Sep monsoon in many states; May heat waves in the north",
            "season_tip": "Hill stations are cooler in summer; coasts are busiest Dec–Jan.",
        }
    if la > 35:
        return {
            "best_seasons": "Late spring through early autumn (milder temperatures)",
            "avoid_seasons": "Mid-winter cold snaps or peak summer heat, depending on latitude",
            "season_tip": "Shoulder seasons often mean fewer crowds and better prices.",
        }
    if la < -15:
        return {
            "best_seasons": "Dry/cooler months (often May–Sep in the southern hemisphere)",
            "avoid_seasons": "Rainy season and peak cyclone/humidity windows",
            "season_tip": "UV is strong year-round — pack sun protection.",
        }
    return {
        "best_seasons": "Dry season / cooler months for your region",
        "avoid_seasons": "Heavy rain or extreme heat spells",
        "season_tip": f"Use the forecast below when packing for {name}.",
    }


def _gemini_guide(
    city_label: str,
    wiki_about: str,
    rag_snippet: str,
    api_key: str,
) -> Optional[Dict[str, str]]:
    client = genai.Client(api_key=api_key)
    context = wiki_about or rag_snippet or city_label
    prompt = (
        f"Destination: {city_label}\n\n"
        f"Context:\n{context[:2000]}\n\n"
        "Return ONLY valid JSON with keys: "
        '"about" (2-3 sentences), "best_seasons", "avoid_seasons", "season_tip" (one short line). '
        "Be practical for first-time visitors. No markdown."
    )
    try:
        _, response = generate_content_with_fallback(
            client,
            DEFAULT_MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json",
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return None
        data = extract_json(text)
        return {
            "about": str(data.get("about", "")).strip(),
            "best_seasons": str(data.get("best_seasons", "")).strip(),
            "avoid_seasons": str(data.get("avoid_seasons", "")).strip(),
            "season_tip": str(data.get("season_tip", "")).strip(),
        }
    except Exception:
        return None


def build_destination_guide(
    city_label: str,
    user_agent: str,
    *,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    label = (city_label or "").strip() or "Destination"
    about = _wikipedia_intro(label, user_agent)
    rag_snippet = ""
    if is_wikivoyage_rag_enabled():
        rag = retrieve_guides(
            label,
            "best time to visit climate weather seasons",
            user_agent,
            top_k=2,
            enabled=True,
        )
        chunks = rag.get("chunks") or []
        if chunks:
            rag_snippet = " ".join(c.get("text", "")[:400] for c in chunks)

    seasons = _rule_seasons(lat, lon, label)
    if api_key and is_destination_guide_ai_enabled():
        ai = _gemini_guide(label, about, rag_snippet, api_key)
        if ai:
            if ai.get("about"):
                about = ai["about"]
            for key in ("best_seasons", "avoid_seasons", "season_tip"):
                if ai.get(key):
                    seasons[key] = ai[key]

    if not about and rag_snippet:
        about = _trim_sentences(rag_snippet, max_chars=480)
    if not about:
        about = (
            f"{label.split(',')[0]} is a popular stop for culture, food, and sightseeing. "
            "Explore the numbered route on the map and swap stops if you want more variety."
        )

    return {
        "city_label": label,
        "about": about,
        "best_seasons": seasons.get("best_seasons", ""),
        "avoid_seasons": seasons.get("avoid_seasons", ""),
        "season_tip": seasons.get("season_tip", ""),
    }


def attach_destination_guide(
    tool_state: Dict[str, Any],
    destination: str,
    user_agent: str,
) -> None:
    """Store destination_guide on tool_state (cached via _guide_key)."""
    dest_key = (destination or "").strip().lower()
    if tool_state.get("_guide_key") == dest_key and tool_state.get("destination_guide"):
        return

    geo = tool_state.get("city_meta") or {}
    hints = tool_state.get("travel_hints") or {}
    label = hints.get("city_label") or destination or geo.get("display_name", "")
    lat = geo.get("lat")
    lon = geo.get("lon")
    dest = hints.get("destination") or {}
    if lat is None and dest.get("lat") is not None:
        lat = dest.get("lat")
    if lon is None and dest.get("lon") is not None:
        lon = dest.get("lon")

    guide = build_destination_guide(
        label,
        user_agent,
        lat=float(lat) if lat is not None else None,
        lon=float(lon) if lon is not None else None,
        api_key=get_gemini_api_key(),
    )
    tool_state["destination_guide"] = guide
    tool_state["_guide_key"] = dest_key
