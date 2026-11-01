"""Map / website / route search links for travel hint cards (no Streamlit)."""

from typing import Any, Dict, List


def _place_map_links(place: Dict[str, Any]) -> List[tuple]:
    links: List[tuple] = []
    if place.get("website_url"):
        links.append(("Website", str(place["website_url"])))
    maps = place.get("maps_url")
    lat, lon = place.get("lat"), place.get("lon")
    if not maps and lat is not None and lon is not None:
        maps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    if maps:
        links.append(("Open in Maps", str(maps)))
    elif place.get("osm_url"):
        links.append(("Map details", str(place["osm_url"])))
    return links


def hint_card_links(place: Dict[str, Any], kind: str = "hotel") -> List[tuple]:
    """One entry point for hotel, transit, and flight cards (kind: hotel | transit | flight)."""
    links = _place_map_links(place)
    if kind == "transit" and place.get("search_url"):
        links.append(("Search routes", str(place["search_url"])))
    if kind == "flight":
        url = place.get("flight_search_url") or place.get("search_url")
        if url:
            links.append(("Search flights", str(url)))
    return links


def hotel_hint_links(hotel: Dict[str, Any]) -> List[tuple]:
    return hint_card_links(hotel, "hotel")


def transport_hint_links(station: Dict[str, Any]) -> List[tuple]:
    return hint_card_links(station, "transit")


def flight_hint_links(airport: Dict[str, Any]) -> List[tuple]:
    return hint_card_links(airport, "flight")
