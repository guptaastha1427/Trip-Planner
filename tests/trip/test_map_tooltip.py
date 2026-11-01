"""Map tooltip must use a light deck.gl container (not default dark popup)."""

import json

from services.trip.map_viz import route_map_tooltip, build_deck


_MIN_ITINERARY = {
    "days": [
        {
            "day": 1,
            "morning": [
                {
                    "name": "Test Museum",
                    "lat": 48.8566,
                    "lon": 2.3522,
                    "category": "museum",
                }
            ],
            "afternoon": [],
            "evening": [],
        }
    ]
}


def test_route_map_tooltip_light_style() -> None:
    tip = route_map_tooltip()
    assert "html" in tip and "style" in tip
    style = tip["style"]
    assert style.get("backgroundColor", "").lower() in ("#ffffff", "#fff", "white")
    assert style.get("color", "").lower() in ("#0f172a", "#000000", "black", "#1e293b")


def test_deck_json_includes_tooltip_style() -> None:
    deck = build_deck(_MIN_ITINERARY)
    assert deck is not None
    spec = json.loads(deck.to_json())
    assert "tooltip" in spec
    assert spec["tooltip"]["style"]["backgroundColor"] == "#ffffff"
    assert deck._tooltip["style"]["backgroundColor"] == "#ffffff"


if __name__ == "__main__":
    test_route_map_tooltip_light_style()
    test_deck_json_includes_tooltip_style()
    print("map tooltip ok")
