"""
Airport, hotel, source/destination, and budget travel hints.

What: Overpass + Wikipedia images + indicative budget price bands.
Why: First-time visitors need airports, stays, and trip endpoints in plain English.
How: Cached Overpass; images via place_images; prices are estimates (not live booking).
"""

import json
import math
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import streamlit as st

from config import OVERPASS_URL
from services.geocoding import geocode_city
from services.http_client import post_text
from services.place_images import (
    enrich_itinerary_with_photos,
    enrich_travel_hints_photos,
    photo_for_place,
    wikimedia_thumbnail,
)
from services.poi_search import _bbox_from_geocode, _osm_poi_id
from services.ui_components import display_city

_PRICE_DISCLAIMER = (
    "Indicative prices only — check booking sites and airlines for live rates."
)


def _normalize_http_url(raw: str) -> Optional[str]:
    s = str(raw).strip()
    if not s or " " in s:
        return None
    if s.startswith("//"):
        s = "https:" + s
    elif not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    return s


def _website_from_tags(tags: Dict[str, Any]) -> Optional[str]:
    for key in (
        "website",
        "contact:website",
        "url",
        "contact:url",
        "booking",
        "contact:booking",
    ):
        val = tags.get(key)
        if not val:
            continue
        url = _normalize_http_url(str(val))
        if url:
            return url
    return None


def _osm_browse_url(el: dict) -> str:
    osm_type = el.get("type", "node")
    osm_id = el.get("id")
    return f"https://www.openstreetmap.org/{osm_type}/{osm_id}"


def _google_maps_url(name: str, city_label: str, lat: float, lon: float) -> str:
    query = quote_plus(f"{name}, {city_label}")
    return f"https://www.google.com/maps/search/?api=1&query={query}"


def _place_name(tags: Dict[str, Any]) -> Optional[str]:
    for key in ("name:en", "int_name", "official_name:en", "alt_name:en", "name"):
        val = tags.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return None


def _coords(el: dict) -> Optional[tuple]:
    lat = el.get("lat")
    lon = el.get("lon")
    if lat is None or lon is None:
        center = el.get("center") or {}
        lat = center.get("lat")
        lon = center.get("lon")
    if lat is None or lon is None:
        return None
    return float(lat), float(lon)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _build_stays_hints_query(south: float, west: float, north: float, east: float) -> str:
    """Airports + hotels — kept separate so stays still load if transit query times out."""
    bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:15];
(
  node["aeroway"~"aerodrome|airport"]({bbox});
  way["aeroway"~"aerodrome|airport"]({bbox});
  node["tourism"~"hotel|hostel|guest_house|motel"]({bbox});
  way["tourism"~"hotel|hostel|guest_house|motel"]({bbox});
);
out center tags;
"""


def _build_transit_hints_query(south: float, west: float, north: float, east: float) -> str:
    bbox = f"{south},{west},{north},{east}"
    return f"""
[out:json][timeout:15];
(
  node["railway"~"station|halt"]({bbox});
  way["railway"~"station|halt"]({bbox});
  node["amenity"="bus_station"]({bbox});
  way["amenity"="bus_station"]({bbox});
  node["public_transport"="station"]["train"="yes"]({bbox});
  node["public_transport"="station"]["bus"="yes"]({bbox});
);
out center tags;
"""


def _merge_overpass_elements(user_agent: str, *queries: str) -> List[dict]:
    seen: set = set()
    out: List[dict] = []
    for query in queries:
        try:
            payload = json.loads(_fetch_hints_raw(query, user_agent))
        except Exception:
            continue
        for el in payload.get("elements", []):
            key = (el.get("type"), el.get("id"))
            if key in seen:
                continue
            seen.add(key)
            out.append(el)
    return out


@st.cache_data(ttl=3600)
def _fetch_hints_raw(query: str, user_agent: str) -> str:
    return post_text(OVERPASS_URL, user_agent, data=query)


def _budget_score(tags: Dict[str, Any], tourism: str) -> int:
    if tourism == "hostel":
        return 0
    if tourism == "guest_house":
        return 1
    if tourism == "motel":
        return 2
    stars = tags.get("stars")
    try:
        return int(float(stars)) + 2
    except (TypeError, ValueError):
        return 5


def _hotel_price_hint(tags: Dict[str, Any], tourism: str) -> str:
    if tourism == "hostel":
        return "Budget · approx ₹700–2,200 / $9–28 per night"
    if tourism in ("guest_house", "motel"):
        return "Budget · approx ₹1,200–3,500 / $15–45 per night"
    stars = tags.get("stars")
    try:
        s = int(float(stars))
    except (TypeError, ValueError):
        return "Mid-range · approx ₹2,500–6,000 / $30–75 per night"
    if s <= 2:
        return "Budget · approx ₹1,500–3,500 / $18–45 per night"
    if s == 3:
        return "Mid-range · approx ₹3,000–7,500 / $35–90 per night"
    return "Premium · approx ₹6,000+ / $75+ per night"


def _airport_price_hint(city_label: str) -> str:
    return (
        f"Flights into {city_label.split(',')[0]}: search airlines for live fares "
        "(often ₹3,000–25,000+ domestic / $80–600+ international, route-dependent). "
        "Airport taxi/prepaid cab to city: often ₹500–2,500 depending on distance."
    )


def _is_train_station(tags: Dict[str, Any]) -> bool:
    railway = tags.get("railway", "")
    if railway in ("station", "halt"):
        return True
    if tags.get("station") == "train":
        return True
    if tags.get("train") == "yes" and tags.get("public_transport") == "station":
        return True
    return False


def _is_bus_station(tags: Dict[str, Any]) -> bool:
    if tags.get("amenity") == "bus_station":
        return True
    if tags.get("bus") == "yes" and tags.get("public_transport") == "station":
        return True
    if tags.get("amenity") == "bus_stop" and tags.get("name") and tags.get("bench") == "yes":
        return False
    return False


def _train_price_hint(city_label: str) -> str:
    return (
        f"Trains to {city_label.split(',')[0]}: compare IRCTC / rail apps for live fares "
        "(Sleeper often ₹400–1,500 · AC chair/3AC ₹800–3,500+ depending on route)."
    )


def _bus_price_hint(city_label: str) -> str:
    return (
        f"Buses to {city_label.split(',')[0]}: check redBus, AbhiBus, or state portals "
        "(often ₹300–1,800 for intercity; shorter hops can be ₹50–400)."
    )


def _intercity_mode_recommendation(distance_km: float) -> str:
    if distance_km < 60:
        return (
            f"About {distance_km:.0f} km apart — bus or cab is usually fastest value; "
            "flying is rarely worth it."
        )
    if distance_km < 250:
        return (
            f"About {distance_km:.0f} km — day bus or train (chair car / sleeper) "
            "often beats flying once you include airport time."
        )
    if distance_km < 700:
        return (
            f"About {distance_km:.0f} km — compare overnight train (sleeper/AC) "
            "with budget flights; trains are often cheaper and more comfortable."
        )
    return (
        f"About {distance_km:.0f} km — flights save time; long-distance trains "
        "(Rajdhani/Garib Rath–style) can still be good value if you book early."
    )


def _train_search_url(origin: str, dest: str) -> str:
    return (
        "https://www.google.com/search?q="
        + quote_plus(f"train {origin} to {dest} IRCTC")
    )


def _bus_search_url(origin: str, dest: str) -> str:
    return (
        "https://www.google.com/search?q="
        + quote_plus(f"bus {origin} to {dest} redbus")
    )


def _flight_search_url(origin: str, dest: str) -> str:
    return "https://www.google.com/travel/flights?q=" + quote_plus(
        f"Flights from {origin} to {dest}"
    )


def _flight_duration_hint(distance_km: Optional[float]) -> str:
    if distance_km is None:
        return (
            "Typical domestic leg: about 1–2 hours in the air, plus roughly "
            "2–3 hours for check-in, security, and baggage each way."
        )
    if distance_km < 200:
        return (
            "Short hop — door-to-door flying often takes longer than train or bus "
            "once you count airport travel and waiting."
        )
    air_hours = max(0.8, float(distance_km) / 650.0)
    return (
        f"Roughly {air_hours:.1f} hours in the air for this distance, plus about "
        "2–3 hours airport time on each end."
    )


def _flight_recommendation(distance_km: Optional[float]) -> str:
    if distance_km is None:
        return (
            "Compare Google Flights or airline apps for live fares, baggage limits, "
            "and morning vs evening slots."
        )
    if distance_km < 200:
        return (
            f"About {distance_km:.0f} km — flights are optional; train or bus is "
            "often simpler for this distance."
        )
    if distance_km < 500:
        return (
            f"About {distance_km:.0f} km — budget airlines can work well if booked "
            "early; compare total time vs overnight train."
        )
    return (
        f"About {distance_km:.0f} km — flying is usually the fastest option. "
        "Book a few weeks ahead and check both primary and secondary airports below."
    )


def _station_remark(name: str, kind: str, city_label: str) -> str:
    label = "Train station" if kind == "train" else "Bus terminal"
    return (
        f"{name} is a nearby {label.lower()} for {city_label}. "
        "Confirm platforms and timings in a booking app before you travel."
    )


def _airport_remark(name: str, city_label: str) -> str:
    return (
        f"{name} is the nearest major airport for {city_label}. "
        "Use official prepaid taxi counters or a trusted ride app to reach your hotel."
    )


def _hotel_remark(name: str, city_label: str, price_hint: str) -> str:
    return (
        f"{name} is listed on OpenStreetMap near {city_label}. "
        f"{price_hint}. Confirm address and reviews in your booking app before paying."
    )


def _geo_endpoint(geo: Dict[str, Any], label: str, role: str) -> Dict[str, Any]:
    return {
        "role": role,
        "label": label,
        "name": label,
        "lat": float(geo["lat"]),
        "lon": float(geo["lon"]),
        "display_name": geo.get("display_name", label),
    }


def fetch_travel_hints(
    geo: Dict[str, Any],
    user_agent: str,
    *,
    city_label: str,
    origin_geo: Optional[Dict[str, Any]] = None,
    origin_label: str = "",
) -> Dict[str, Any]:
    south, west, north, east = _bbox_from_geocode(geo, padding=0.12)
    airports: List[dict] = []
    hotels: List[dict] = []
    train_stations: List[dict] = []
    bus_stations: List[dict] = []

    elements = _merge_overpass_elements(
        user_agent,
        _build_stays_hints_query(south, west, north, east),
        _build_transit_hints_query(south, west, north, east),
    )

    dest_lat, dest_lon = float(geo["lat"]), float(geo["lon"])

    for el in elements:
        tags = el.get("tags") or {}
        name = _place_name(tags)
        if not name:
            continue
        coords = _coords(el)
        if not coords:
            continue
        lat, lon = coords
        aeroway = tags.get("aeroway", "")
        tourism = tags.get("tourism", "")
        entry: Dict[str, Any] = {
            "poi_id": _osm_poi_id(el),
            "name": name,
            "lat": lat,
            "lon": lon,
            "distance_km": round(_haversine_km(dest_lat, dest_lon, lat, lon), 1),
        }
        if aeroway in ("aerodrome", "airport") or tags.get("aeroway"):
            entry["remark"] = _airport_remark(name, city_label)
            entry["price_hint"] = _airport_price_hint(city_label)
            entry["budget_friendly"] = True
            entry["website_url"] = _website_from_tags(tags)
            entry["maps_url"] = _google_maps_url(name, city_label, lat, lon)
            entry["osm_url"] = _osm_browse_url(el)
            iata = tags.get("iata") or tags.get("ref")
            if iata and len(str(iata).strip()) <= 4:
                entry["iata"] = str(iata).strip().upper()
            airports.append(entry)
        elif tourism in ("hotel", "hostel", "guest_house", "motel"):
            score = _budget_score(tags, tourism)
            entry["tourism"] = tourism
            entry["budget_score"] = score
            entry["budget_friendly"] = score <= 4
            entry["price_hint"] = _hotel_price_hint(tags, tourism)
            entry["remark"] = _hotel_remark(name, city_label, entry["price_hint"])
            entry["website_url"] = _website_from_tags(tags)
            entry["maps_url"] = _google_maps_url(name, city_label, lat, lon)
            entry["osm_url"] = _osm_browse_url(el)
            hotels.append(entry)
        elif _is_train_station(tags):
            entry["kind"] = "train"
            entry["price_hint"] = _train_price_hint(city_label)
            entry["remark"] = _station_remark(name, "train", city_label)
            entry["website_url"] = _website_from_tags(tags)
            entry["maps_url"] = _google_maps_url(name, city_label, lat, lon)
            entry["osm_url"] = _osm_browse_url(el)
            train_stations.append(entry)
        elif _is_bus_station(tags):
            entry["kind"] = "bus"
            entry["price_hint"] = _bus_price_hint(city_label)
            entry["remark"] = _station_remark(name, "bus", city_label)
            entry["website_url"] = _website_from_tags(tags)
            entry["maps_url"] = _google_maps_url(name, city_label, lat, lon)
            entry["osm_url"] = _osm_browse_url(el)
            bus_stations.append(entry)

    airports.sort(key=lambda a: a.get("distance_km", 999))
    train_stations.sort(key=lambda s: s.get("distance_km", 999))
    bus_stations.sort(key=lambda s: s.get("distance_km", 999))
    hotels.sort(key=lambda h: (h.get("budget_score", 9), h.get("distance_km", 999)))
    airports = airports[:3]
    budget_hotels = [h for h in hotels if h.get("budget_friendly")][:5]
    if not budget_hotels:
        budget_hotels = hotels[:5]
    train_stations = train_stations[:5]
    bus_stations = bus_stations[:5]

    dest_label = display_city(city_label.strip() or geo.get("display_name", "Destination"))
    origin_display = display_city(origin_label.strip()) if origin_label.strip() else ""
    destination = _geo_endpoint(geo, dest_label, "destination")
    destination["image_url"] = wikimedia_thumbnail(dest_label, user_agent)

    source: Optional[Dict[str, Any]] = None
    if origin_geo and origin_display:
        source = _geo_endpoint(origin_geo, origin_display, "source")
        source["image_url"] = wikimedia_thumbnail(origin_display, user_agent)
        source["price_hint"] = (
            "Travel from your home city: compare trains, buses, and flights for live fares."
        )

    for ap in airports[:2]:
        ap["image_url"] = photo_for_place(ap["name"], city_label, user_agent)
    for ht in budget_hotels[:4]:
        ht["image_url"] = photo_for_place(ht["name"], city_label, user_agent)

    intercity_km: Optional[float] = None
    mode_recommendation: Optional[str] = None
    train_route_search: Optional[str] = None
    bus_route_search: Optional[str] = None
    flight_route_search: Optional[str] = None
    flight_details: Dict[str, Any] = {
        "destination": dest_label,
        "fare_hint": _airport_price_hint(city_label),
        "duration_hint": _flight_duration_hint(None),
        "recommendation": (
            "Fill in From on the plan form to open route-specific flight search."
        ),
    }
    if origin_geo and origin_display:
        intercity_km = round(
            _haversine_km(
                float(origin_geo["lat"]),
                float(origin_geo["lon"]),
                dest_lat,
                dest_lon,
            ),
            0,
        )
        mode_recommendation = _intercity_mode_recommendation(float(intercity_km))
        train_route_search = _train_search_url(origin_display, dest_label)
        bus_route_search = _bus_search_url(origin_display, dest_label)
        flight_route_search = _flight_search_url(origin_display, dest_label)
        flight_details = {
            "origin": origin_display,
            "destination": dest_label,
            "distance_km": intercity_km,
            "duration_hint": _flight_duration_hint(
                float(intercity_km) if intercity_km is not None else None
            ),
            "recommendation": _flight_recommendation(
                float(intercity_km) if intercity_km is not None else None
            ),
            "fare_hint": _airport_price_hint(city_label),
            "google_flights_url": flight_route_search,
        }
        for stn in train_stations[:4]:
            stn["search_url"] = train_route_search
        for stn in bus_stations[:4]:
            stn["search_url"] = bus_route_search
        for ap in airports:
            ap["flight_search_url"] = flight_route_search

    nearest_airport = airports[0] if airports else None
    nearest_train = train_stations[0] if train_stations else None
    nearest_bus = bus_stations[0] if bus_stations else None

    trip_from = origin_display or "Your city"
    tips = [
        f"Trip: {trip_from} → {dest_label} (see map markers).",
        "Follow numbered stops on the map in order; orange arcs show direction to the next place.",
        _PRICE_DISCLAIMER,
    ]
    if mode_recommendation:
        tips.append(f"Getting there: {mode_recommendation}")
    if nearest_train:
        tips.append(
            f"By train? {nearest_train['name']} is about "
            f"{nearest_train.get('distance_km', '?')} km from the city center — use Search routes for timetables."
        )
    if nearest_bus:
        tips.append(
            f"By bus? {nearest_bus['name']} is about "
            f"{nearest_bus.get('distance_km', '?')} km from the center — compare operators online."
        )
    if nearest_airport:
        tips.append(
            f"Flying in? Land at {nearest_airport['name']} "
            f"({nearest_airport.get('distance_km', '?')} km from city center), then head to your hotel or Stop 1."
        )
    if flight_route_search and origin_display:
        tips.append(
            f"Flights {origin_display} → {dest_label}: use the Flights section for search links and airport pick-up tips."
        )
    if budget_hotels:
        tips.append(
            f"Budget stays: try {budget_hotels[0]['name']} "
            f"({budget_hotels[0].get('price_hint', '')})."
        )

    return {
        "city_label": city_label,
        "destination": destination,
        "source": source,
        "nearest_airport": nearest_airport,
        "airports": airports,
        "hotels": hotels,
        "budget_hotels": budget_hotels,
        "train_stations": train_stations,
        "bus_stations": bus_stations,
        "nearest_train": nearest_train,
        "nearest_bus": nearest_bus,
        "intercity_distance_km": intercity_km,
        "mode_recommendation": mode_recommendation,
        "train_route_search": train_route_search,
        "bus_route_search": bus_route_search,
        "flight_route_search": flight_route_search,
        "flight_details": flight_details,
        "tips": tips,
        "price_disclaimer": _PRICE_DISCLAIMER,
    }


def attach_travel_hints(
    tool_state: Dict[str, Any],
    destination: str,
    user_agent: str,
) -> None:
    """Mutate tool_state with travel_hints when geodata is available."""
    origin_label = (tool_state.get("origin_city") or "").strip()
    geo = tool_state.get("city_meta")
    if not geo:
        geo = geocode_city(destination, user_agent)
        if geo:
            tool_state["city_meta"] = geo

    origin_geo = None
    if origin_label:
        origin_geo = geocode_city(origin_label, user_agent)
        if origin_geo:
            tool_state["origin_meta"] = origin_geo

    if not geo:
        tool_state["travel_hints"] = {
            "city_label": destination,
            "destination": None,
            "source": None,
            "airports": [],
            "hotels": [],
            "budget_hotels": [],
            "train_stations": [],
            "bus_stations": [],
            "tips": [
                "Could not load airport/hotel hints. You can still use the numbered route on the map.",
            ],
            "price_disclaimer": _PRICE_DISCLAIMER,
        }
        return

    label = destination.strip() or geo.get("display_name", "your destination")
    hints = fetch_travel_hints(
        geo,
        user_agent,
        city_label=label,
        origin_geo=origin_geo,
        origin_label=origin_label,
    )
    tool_state["travel_hints"] = enrich_travel_hints_photos(hints, user_agent)


# Re-export for app
def enrich_itinerary_photos(
    itinerary: Dict[str, Any],
    city_label: str,
    user_agent: str,
) -> Dict[str, Any]:
    return enrich_itinerary_with_photos(itinerary, city_label, user_agent)
