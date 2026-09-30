"""
Lightweight connectivity checks for setup / sidebar diagnostics.

What: Ping Nominatim and Overpass with tiny queries.
Why: Capstone step 1 asks to verify API connections and User-Agent headers.
How: Returns human-readable status strings (no exceptions to the UI).
"""

from config import NOMINATIM_URL, OVERPASS_URL
from services.http_client import get_json, post_text


def test_nominatim(user_agent: str) -> str:
    if not user_agent:
        return "Missing User-Agent — add your contact email in the sidebar."
    try:
        data = get_json(
            NOMINATIM_URL,
            user_agent,
            params={"q": "London", "format": "json", "limit": 1},
            use_nominatim_limit=True,
        )
        if data:
            return f"OK — Nominatim returned: {data[0].get('display_name', 'result')[:60]}…"
        return "Nominatim responded but found no results for 'London'."
    except Exception as exc:  # noqa: BLE001
        return f"Nominatim error: {exc}"


def test_overpass(user_agent: str) -> str:
    if not user_agent:
        return "Missing User-Agent — add your contact email in the sidebar."
    tiny = '[out:json][timeout:10];node(51.5,-0.2,51.6,0.0)["tourism"="museum"];out 1;'
    try:
        text = post_text(OVERPASS_URL, user_agent, data=tiny)
        if '"elements"' in text:
            return "OK — Overpass API returned JSON."
        return "Overpass returned unexpected body."
    except Exception as exc:  # noqa: BLE001
        return f"Overpass error: {exc}"
