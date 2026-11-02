"""Illustrative stay and route examples when OSM data is sparse (not live bookings)."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

_ILLUSTRATIVE_NOTE = (
    "Examples only — verify names, prices, and availability on maps or booking apps."
)


def _norm_place(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    return s.split()[0] if s.split() else ""


def _route_key(origin: str, destination: str) -> Tuple[str, str]:
    return (_norm_place(origin), _norm_place(destination))


# Popular India demo routes (capstone illustrations, not scraped prices).
_ROUTE_TRANSPORT_EXAMPLES: Dict[Tuple[str, str], Dict[str, List[str]]] = {
    ("mumbai", "goa"): {
        "flights": [
            "Mumbai (BOM) → Goa (GOX/Mopa or GOI): IndiGo, SpiceJet, Air India — "
            "typical block time ~1h; morning flights often beat weekend traffic.",
        ],
        "trains": [
            "Konkan Railway: CSMT or LTT → Madgaon (MAO) or Thivim — "
            "Sleeper/3AC; book IRCTC (Mandovi/Ganpati Special–style services on route).",
        ],
        "buses": [
            "Overnight AC Volvo: Mumbai → Panaji/Mapusa — operators like Neeta, Paulo "
            "(compare on redBus / AbhiBus).",
        ],
    },
    ("delhi", "jaipur"): {
        "flights": ["Delhi (DEL) → Jaipur (JAI): ~1h; frequent budget carriers."],
        "trains": ["New Delhi → Jaipur Junction: Shatabdi / superfast chair car (IRCTC)."],
        "buses": ["Delhi → Jaipur AC seater/sleeper on redBus (6–7h road)."],
    },
    ("chennai", "bengaluru"): {
        "flights": ["Chennai (MAA) → Bengaluru (BLR): very frequent 1h hops."],
        "trains": ["Chennai Central → KSR Bengaluru: Brindavan/Shatabdi-style day trains."],
        "buses": ["Overnight and day buses via redBus (6–8h depending on service)."],
    },
}

_STAY_EXAMPLES: Dict[str, List[Dict[str, Any]]] = {
    "goa": [
        {
            "name": "Calangute / Baga guesthouses",
            "tourism": "guest_house",
            "distance_km": None,
            "price_hint": "Budget · approx ₹1,200–3,500 / night (area average)",
            "remark": "North Goa beach belt — many small guesthouses; book via maps/reviews.",
            "illustrative": True,
        },
        {
            "name": "Panaji / Fontainhas homestays",
            "tourism": "guest_house",
            "distance_km": None,
            "price_hint": "Mid-range · approx ₹2,500–5,500 / night",
            "remark": "Quieter than beach strip; good for food and heritage walks.",
            "illustrative": True,
        },
    ],
    "jaipur": [
        {
            "name": "Hathroi / MI Road budget hotels",
            "tourism": "hotel",
            "distance_km": None,
            "price_hint": "Budget · approx ₹1,500–3,500 / night",
            "remark": "Central access to Old City and forts day trips.",
            "illustrative": True,
        },
    ],
    "bengaluru": [
        {
            "name": "Indiranagar / Koramangala hostels",
            "tourism": "hostel",
            "distance_km": None,
            "price_hint": "Budget · approx ₹700–2,200 / night",
            "remark": "Cafe and metro access; compare on hostel booking apps.",
            "illustrative": True,
        },
    ],
}


def illustrative_transport_examples(
    origin_label: str,
    destination_label: str,
) -> Dict[str, List[str]]:
    """Route-specific sample trains/buses/flights (always verify live)."""
    key = _route_key(origin_label, destination_label)
    rev = (key[1], key[0])
    if key in _ROUTE_TRANSPORT_EXAMPLES:
        return dict(_ROUTE_TRANSPORT_EXAMPLES[key])
    if rev in _ROUTE_TRANSPORT_EXAMPLES:
        return dict(_ROUTE_TRANSPORT_EXAMPLES[rev])
    o = origin_label or "your city"
    d = destination_label or "destination"
    return {
        "flights": [
            f"Search: {o} → {d} on Google Flights — compare 2–3 airlines for baggage and timing.",
        ],
        "trains": [
            f"Search: train {o} to {d} on IRCTC or Rail apps — sleeper vs AC chair for overnight legs.",
        ],
        "buses": [
            f"Search: AC bus {o} to {d} on redBus / state transport sites — overnight often saves a hotel night.",
        ],
    }


def illustrative_stay_examples(destination_label: str) -> List[Dict[str, Any]]:
    """Fallback stay cards when Overpass returns no tourism=hotel tags."""
    dest = _norm_place(destination_label)
    for key, rows in _STAY_EXAMPLES.items():
        if key in dest or dest in key:
            return [dict(r) for r in rows]
    city = destination_label.split(",")[0].strip() or "your destination"
    return [
        {
            "name": f"Budget hotels near {city} center",
            "tourism": "hotel",
            "distance_km": None,
            "price_hint": "Budget · approx ₹1,500–3,500 / night (area average)",
            "remark": (
                f"Search Google Maps or Booking.com for guesthouses in {city}. "
                f"{_ILLUSTRATIVE_NOTE}"
            ),
            "illustrative": True,
        },
        {
            "name": f"Hostels / guesthouses ({city})",
            "tourism": "hostel",
            "distance_km": None,
            "price_hint": "Budget · approx ₹700–2,200 / night",
            "remark": "Filter for reviews and distance to your Day 1 stops on the map.",
            "illustrative": True,
        },
    ]


def merge_illustrative_hints(
    hints: Dict[str, Any],
    *,
    origin_label: str,
    destination_label: str,
) -> None:
    """Attach examples in-place when OSM lists are empty."""
    if not hints.get("budget_hotels") and not hints.get("hotels"):
        hints["illustrative_stays"] = illustrative_stay_examples(destination_label)
    else:
        hints["illustrative_stays"] = []
    hints["transport_examples"] = illustrative_transport_examples(
        origin_label,
        destination_label,
    )
    hints["examples_note"] = _ILLUSTRATIVE_NOTE
