"""Streamlit UI for booking demo travel packages."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from services.bookings import create_package_booking
from services.demo_dashboard import is_admin_dashboard_mode
from services.travel_packages import (
    FARE_TIERS,
    PACKAGE_BOOKING_PREFILL_KEY,
    estimate_package_breakdown,
    get_package,
    list_packages,
)
from services.ui_components import section_heading

_PKG_CONFIRMED_FLASH = "pkg_booking_confirmed_flash"
_PKG_CONFIRMED_SNAPSHOT = "pkg_booking_confirmed_snapshot"


def _package_form_snapshot(
    package_id: str,
    origin: str,
    destination: str,
    departure: date,
    travelers: int,
    nights: int,
    fare_tier: str,
) -> tuple:
    return (
        package_id,
        origin.strip(),
        destination.strip(),
        departure.isoformat(),
        int(travelers),
        int(nights),
        fare_tier,
    )


def _apply_prefill_to_widget_state(prefill: dict, pkg_ids: list[str]) -> None:
    pid = prefill.get("package_id", "custom_trip")
    if pid not in pkg_ids:
        pid = pkg_ids[0]
    st.session_state["pkg_picked_id"] = pid
    st.session_state["pkg_origin"] = prefill.get("origin", "")
    st.session_state["pkg_destination"] = prefill.get("destination", "")
    st.session_state["pkg_nights"] = int(prefill.get("nights", 1))
    st.session_state.pop(PACKAGE_BOOKING_PREFILL_KEY, None)
    st.session_state.pop(_PKG_CONFIRMED_SNAPSHOT, None)


def render_book_package_tab(user_id: str) -> None:
    confirmed = st.session_state.pop(_PKG_CONFIRMED_FLASH, None)
    if confirmed:
        st.success(
            f"**Package confirmed!** Reference **{confirmed.get('booking_id')}** — "
            f"₹{confirmed.get('booked_amount', 0):,.0f}. "
            f"Open the **My bookings** tab to view it."
        )

    section_heading("Book a travel package", variant="travel")
    st.caption(
        "Bundled trips are simulated — no payment is processed. "
        "The estimate below updates as you change package, travelers, nights, or fare. "
        "Read **Terms & Policies** in the sidebar for package pricing, cancellation, and refund rules."
    )

    if is_admin_dashboard_mode():
        st.caption(
            "Admin mode: package is booked for the **sidebar account** you are previewing."
        )

    prefill = st.session_state.get(PACKAGE_BOOKING_PREFILL_KEY)
    packages = list_packages()
    pkg_ids = [p.package_id for p in packages]

    if prefill and isinstance(prefill, dict):
        st.success(
            f"Prefilled from Trip Planner: **{prefill.get('destination')}** "
            f"({prefill.get('nights', 1)} night). Adjust details below."
        )
        _apply_prefill_to_widget_state(prefill, pkg_ids)

    default_pkg = st.session_state.get("pkg_picked_id", "weekend_escape")
    if default_pkg not in pkg_ids:
        default_pkg = pkg_ids[0]

    picked_id = st.selectbox(
        "Package",
        options=pkg_ids,
        index=pkg_ids.index(default_pkg) if default_pkg in pkg_ids else 0,
        format_func=lambda pid: f"{get_package(pid).name} — {get_package(pid).tagline}",
        key="pkg_picked_id",
    )
    pkg = get_package(picked_id)
    assert pkg

    pkg_defaults = st.session_state.get("_pkg_last_id")
    if pkg_defaults != picked_id:
        st.session_state.setdefault("pkg_origin", pkg.default_origin)
        st.session_state.setdefault("pkg_destination", pkg.default_destination)
        st.session_state.setdefault("pkg_nights", pkg.nights)
        if pkg_defaults is not None:
            st.session_state["pkg_origin"] = pkg.default_origin
            st.session_state["pkg_destination"] = pkg.default_destination
            st.session_state["pkg_nights"] = pkg.nights
        st.session_state["_pkg_last_id"] = picked_id

    c1, c2 = st.columns(2)
    origin = c1.text_input("From", key="pkg_origin")
    destination = c2.text_input("To", key="pkg_destination")

    c3, c4, c5 = st.columns(3)
    departure = c3.date_input(
        "Departure date",
        value=date.today() + timedelta(days=14),
        min_value=date.today() + timedelta(days=1),
        key="pkg_departure",
    )
    travelers = c4.number_input(
        "Travelers", min_value=1, max_value=8, value=2, key="pkg_travelers"
    )
    nights = c5.number_input(
        "Nights", min_value=1, max_value=14, value=int(pkg.nights), key="pkg_nights"
    )

    fare_tier = st.radio(
        "Fare type",
        options=list(FARE_TIERS.keys()),
        format_func=lambda k: FARE_TIERS[k][3],
        horizontal=True,
        key="pkg_fare_tier",
    )

    breakdown = estimate_package_breakdown(
        pkg, int(travelers), fare_tier, nights=int(nights)
    )
    st.markdown("##### Estimated price")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", f"₹{breakdown['total']:,.0f}")
    m2.metric("Per person", f"₹{breakdown['per_person']:,.0f}")
    m3.metric("Base (all travelers)", f"₹{breakdown['base_subtotal']:,.0f}")
    extra = breakdown["fare_adjustment"] + breakdown["nights_extra"]
    m4.metric("Extras (fare + nights)", f"₹{extra:,.0f}")

    tier_label = FARE_TIERS[fare_tier][3]
    st.caption(
        f"{tier_label} · **{int(travelers)}** traveler(s) · **{int(nights)}** night(s) · "
        f"Includes: {', '.join(i.replace('_', ' ') for i in pkg.includes)}"
    )
    if breakdown["nights_extra"] > 0:
        st.caption(
            f"Night add-on: ₹{breakdown['nights_extra']:,.0f} "
            f"(₹1,200 × extra nights beyond 2 × travelers)"
        )

    form_snapshot = _package_form_snapshot(
        picked_id, origin, destination, departure, int(travelers), int(nights), fare_tier
    )
    confirmed_snap = st.session_state.get(_PKG_CONFIRMED_SNAPSHOT)
    package_confirmed = (
        isinstance(confirmed_snap, dict)
        and confirmed_snap.get("form") == form_snapshot
    )

    if package_confirmed:
        ref = confirmed_snap.get("booking_id", "")
        st.button("Package confirmed", type="primary", key="pkg_confirm", disabled=True)
        if ref:
            st.caption(f"Booking reference **{ref}** — change any field above to book again.")
    elif st.button("Confirm package booking", type="primary", key="pkg_confirm"):
        if not origin.strip() or not destination.strip():
            st.error("Please enter origin and destination.")
        else:
            try:
                booking = create_package_booking(
                    user_id,
                    picked_id,
                    origin,
                    destination,
                    departure,
                    int(travelers),
                    fare_tier,
                    nights=int(nights),
                )
            except Exception as exc:
                st.error(f"Could not save booking: {exc}")
            else:
                st.session_state[_PKG_CONFIRMED_SNAPSHOT] = {
                    "form": form_snapshot,
                    "booking_id": booking.get("booking_id"),
                }
                st.session_state[_PKG_CONFIRMED_FLASH] = booking
                st.balloons()
                st.rerun()

    st.markdown("**Available packages**")
    for p in packages:
        with st.expander(p.name):
            st.write(p.tagline)
            st.caption(
                f"From **{p.default_origin}** to **{p.default_destination}** · "
                f"{p.nights} nights · from ₹{p.base_price_per_person:,.0f} / person (standard)"
            )
