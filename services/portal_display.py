"""Shared copy for refund and support ticket UI."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from services.bookings import enrich_booking_display, get_booking
from services.refund_policy_config import REFUND_REASONS
from services.ui_copy import polish_ui_copy

_REFUND_REASON_LABELS = dict(REFUND_REASONS)


def refund_reason_label(reason_code: str) -> str:
    if not reason_code:
        return "—"
    return _REFUND_REASON_LABELS.get(reason_code, str(reason_code).replace("_", " ").title())


def format_portal_datetime(raw: str) -> str:
    if not raw:
        return "—"
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).strftime(
            "%d %b %Y, %H:%M"
        )
    except ValueError:
        return str(raw)


def booking_for_refund_display(booking_id: str) -> Optional[Dict[str, Any]]:
    row = get_booking(booking_id)
    if not row:
        return None
    return enrich_booking_display(row)


def booking_detail_markdown(booking: Dict[str, Any]) -> str:
    """Human-readable booking / travel ticket summary."""
    lines: List[str] = []
    title = booking.get("display_title")
    if title:
        lines.append(f"**{title}**")
    else:
        lines.append(
            f"**{booking.get('booking_id')}** · "
            f"{booking.get('origin', '—')} → {booking.get('destination', '—')}"
        )
    lines.append(
        f"- **Booking status:** {str(booking.get('status', '—')).title()}"
    )
    lines.append(
        f"- **Travel:** {str(booking.get('travel_mode', '—')).title()} · "
        f"**Ticket / fare:** {booking.get('ticket_type', '—')}"
    )
    if booking.get("package_name"):
        lines.append(
            f"- **Package:** {booking.get('package_name')} "
            f"({booking.get('travelers', 1)} traveler(s), "
            f"{booking.get('nights', '—')} nights)"
        )
    lines.append(
        f"- **Journey:** {format_portal_datetime(booking.get('journey_datetime', ''))}"
    )
    lines.append(f"- **Amount paid:** ₹{booking.get('booked_amount', 0):,.0f}")
    pol = booking.get("policy_label") or (booking.get("policy") or {}).get("policy_id")
    if pol:
        lines.append(f"- **Refund policy:** {pol}")
    return polish_ui_copy("\n".join(lines))


def ticket_why_raised_markdown(ticket: Dict[str, Any]) -> str:
    """Context for admins: why the customer opened the ticket."""
    messages = ticket.get("messages") or []
    first_user = next((m for m in messages if m.get("from") == "user"), None)
    initial_body = (first_user or {}).get("body") or "—"
    created = format_portal_datetime(ticket.get("created_at", ""))
    lines = [
        f"- **Category:** {ticket.get('category', '—')}",
        f"- **Subject:** {ticket.get('subject', '—')}",
        f"- **Opened:** {created}",
        f"- **Customer description:** {initial_body}",
    ]
    return polish_ui_copy("\n".join(lines))
