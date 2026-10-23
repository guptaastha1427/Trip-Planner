"""
Demo booking catalog — static JSON plus user-created package bookings in portal state.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from config import DEMO_BOOKINGS_PATH
from services.refund_policy_config import get_policy, policy_as_dict
from services.ui_copy import polish_ui_copy
from services.travel_packages import (
    FARE_TIERS,
    PACKAGE_MAX_TRAVELERS,
    estimate_package_total,
    get_package,
    journey_iso,
)


def _load_catalog() -> Dict[str, Any]:
    if not DEMO_BOOKINGS_PATH.is_file():
        return {"bookings": []}
    try:
        return json.loads(DEMO_BOOKINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"bookings": []}


def _all_static_bookings() -> List[Dict[str, Any]]:
    return [dict(b) for b in _load_catalog().get("bookings", [])]


def _user_created_bookings() -> List[Dict[str, Any]]:
    from services.customer_portal_store import list_user_bookings

    return list_user_bookings()


def _catalog_booking_order() -> Dict[str, int]:
    order: Dict[str, int] = {}
    for i, row in enumerate(_load_catalog().get("bookings", [])):
        bid = row.get("booking_id")
        if bid:
            order[str(bid)] = i
    return order


def _booked_at_sort_key(row: Dict[str, Any], catalog_order: Dict[str, int]) -> datetime:
    """When the booking was made (not journey departure)."""
    raw = row.get("created_at")
    if raw:
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        except ValueError:
            pass
    bid = str(row.get("booking_id", ""))
    if bid in catalog_order:
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        return base + timedelta(seconds=catalog_order[bid])
    jdt = parse_journey_dt(row)
    if jdt:
        if jdt.tzinfo is None:
            jdt = jdt.replace(tzinfo=timezone.utc)
        return jdt
    return datetime.min.replace(tzinfo=timezone.utc)


def get_booking(booking_id: str) -> Optional[Dict[str, Any]]:
    for row in _all_static_bookings():
        if row.get("booking_id") == booking_id:
            return row
    for row in _user_created_bookings():
        if row.get("booking_id") == booking_id:
            return dict(row)
    return None


def list_bookings_for_user(user_id: str) -> List[Dict[str, Any]]:
    catalog_order = _catalog_booking_order()
    rows = [b for b in _all_static_bookings() if b.get("user_id") == user_id]
    rows.extend(b for b in _user_created_bookings() if b.get("user_id") == user_id)
    rows.sort(
        key=lambda r: _booked_at_sort_key(r, catalog_order),
        reverse=True,
    )
    return rows


def parse_journey_dt(booking: Dict[str, Any]) -> Optional[datetime]:
    raw = booking.get("journey_datetime")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None


def enrich_booking_display(booking: Dict[str, Any]) -> Dict[str, Any]:
    """Attach policy summary for UI tables."""
    out = dict(booking)
    policy = get_policy(str(booking.get("policy_id", "")))
    if policy:
        out["policy"] = policy_as_dict(policy)
        out["policy_label"] = policy.label
        jdt = parse_journey_dt(booking)
        if jdt:
            from datetime import timedelta

            deadline = jdt - timedelta(hours=policy.min_hours_before_departure)
            out["cancellation_deadline"] = deadline.isoformat(timespec="minutes")
    if booking.get("package_name"):
        out["display_title"] = (
            f"{booking.get('booking_id')} · {booking.get('package_name')} · "
            f"{booking.get('origin')} → {booking.get('destination')}"
        )
    if out.get("operator"):
        out["operator"] = polish_ui_copy(str(out["operator"]))
    if out.get("policy_label"):
        out["policy_label"] = polish_ui_copy(str(out["policy_label"]))
    if out.get("policy") and isinstance(out["policy"], dict) and out["policy"].get("description"):
        out["policy"] = dict(out["policy"])
        out["policy"]["description"] = polish_ui_copy(str(out["policy"]["description"]))
    return out


def create_package_booking(
    user_id: str,
    package_id: str,
    origin: str,
    destination: str,
    departure_date,
    travelers: int,
    fare_tier: str,
    *,
    nights: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a confirmed demo package booking (no real payment)."""
    from services.customer_portal_store import add_user_booking, new_id

    pkg = get_package(package_id)
    if not pkg:
        raise ValueError(f"Unknown package: {package_id}")
    tier = FARE_TIERS.get(fare_tier, FARE_TIERS["standard"])
    policy_id, ticket_type, _, _ = tier
    nights_val = nights if nights is not None else pkg.nights
    headcount = max(1, min(PACKAGE_MAX_TRAVELERS, int(travelers)))
    amount = estimate_package_total(pkg, headcount, fare_tier, nights=nights_val)
    booking_id = new_id("BK-PKG")
    record = {
        "booking_id": booking_id,
        "user_id": user_id,
        "status": "confirmed",
        "travel_mode": "package",
        "ticket_type": ticket_type,
        "policy_id": policy_id,
        "origin": origin.strip(),
        "destination": destination.strip(),
        "journey_datetime": journey_iso(departure_date),
        "booked_amount": amount,
        "currency": "INR",
        "operator": pkg.operator,
        "package_id": pkg.package_id,
        "package_name": pkg.name,
        "package_tagline": pkg.tagline,
        "travelers": headcount,
        "nights": nights_val,
        "includes": list(pkg.includes),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    return add_user_booking(record)
