"""Thomas Cook–style package summary cards (presentation only)."""

from __future__ import annotations

import html
from typing import Optional

import streamlit as st

from services.travel_packages import (
    PackageDetail,
    TravelPackage,
    catalog_route_label,
    package_nights_days_badge,
)
from services.ui_nav_chips import nav_chip_row_html


def _emit_html(fragment: str) -> None:
    """Render HTML without Markdown interpreting indented blocks as code."""
    st.html(fragment.strip())


def _badge_chip(label: str, variant: str = "") -> str:
    safe = html.escape(label.strip())
    extra = f" pkg-badge--{variant}" if variant else ""
    return f'<span class="pkg-badge{extra}">{safe}</span>'


def _day_card_html(day) -> str:
    sights = "".join(
        f"<li>{html.escape(s)}</li>" for s in (day.sightseeing or ())
    )
    meals = "".join(f"<li>{html.escape(m)}</li>" for m in (day.meals or ()))
    hotel = html.escape(day.hotel or "—")
    title = html.escape(day.title or "")
    summary = html.escape(day.summary or "")
    summary_html = (
        f'<p class="pkg-day-card__summary">{summary}</p>' if summary else ""
    )
    num = int(day.day_number)
    return (
        f'<article class="pkg-day-card">'
        f'<div class="pkg-day-card__banner">Day {num} · {title}</div>'
        f'<div class="pkg-day-card__body">{summary_html}'
        f'<div class="pkg-day-card__item">'
        f'<span class="pkg-day-card__ico pkg-day-card__ico--stay" aria-hidden="true"></span>'
        f'<div><p class="pkg-day-card__item-label">Stay</p>'
        f'<p class="pkg-day-card__item-value">{hotel}</p></div></div>'
        f'<div class="pkg-day-card__item">'
        f'<span class="pkg-day-card__ico pkg-day-card__ico--sight" aria-hidden="true"></span>'
        f'<div><p class="pkg-day-card__item-label">Sightseeing</p>'
        f'<ul class="pkg-day-card__list">{sights or "<li>Leisure / transfer</li>"}</ul>'
        f"</div></div>"
        f'<div class="pkg-day-card__item">'
        f'<span class="pkg-day-card__ico pkg-day-card__ico--meal" aria-hidden="true"></span>'
        f'<div><p class="pkg-day-card__item-label">Meals</p>'
        f'<ul class="pkg-day-card__list">{meals or "<li>On your own</li>"}</ul>'
        f"</div></div></div></article>"
    )


def package_detail_badges_html(pkg: TravelPackage, detail: Optional[PackageDetail]) -> str:
    chips = [_badge_chip(package_nights_days_badge(pkg.nights), "duration")]
    if detail and detail.tour_type:
        chips.append(_badge_chip(detail.tour_type, "type"))
    chips.append(_badge_chip(catalog_route_label(pkg), "route"))
    for split in (detail.night_splits if detail else ()):
        chips.append(_badge_chip(split, "city"))
    return f'<div class="pkg-badge-row">{"".join(chips)}</div>'


def package_highlights_html(detail: PackageDetail) -> str:
    items = "".join(f"<li>{html.escape(h)}</li>" for h in detail.highlights)
    return f'<ul class="pkg-highlights">{items}</ul>'


def package_day_breakdown_html(detail: PackageDetail) -> str:
    if not detail.days:
        return ""
    cards = "".join(_day_card_html(day) for day in detail.days)
    return (
        f'<p class="pkg-summary-bar">Day-wise summary</p>'
        f'<section class="pkg-day-breakdown">{cards}</section>'
    )


def package_inclusions_html(detail: PackageDetail) -> str:
    return (
        f'<div class="pkg-info-block">'
        f"<p><strong>Accommodation</strong><br>{html.escape(detail.accommodation)}</p>"
        f"<p><strong>Transport</strong><br>{html.escape(detail.transport)}</p>"
        f"<p><strong>Meals</strong><br>{html.escape(detail.meals)}</p>"
        f"<p><strong>Sightseeing</strong><br>{html.escape(detail.sightseeing)}</p>"
        f"<p><strong>Exclusions</strong><br>{html.escape(detail.exclusions)}</p>"
        f"</div>"
    )


def _section_card_html(banner: str, inner_html: str) -> str:
    return (
        f'<article class="pkg-day-card pkg-section-card">'
        f'<div class="pkg-day-card__banner">{html.escape(banner)}</div>'
        f'<div class="pkg-day-card__body">{inner_html}</div>'
        f"</article>"
    )


def package_detail_body_html(
    detail: PackageDetail, *, compact: bool, include_nav: bool = True
) -> str:
    """Full left column — HTML only (no Streamlit tabs; avoids nesting booking widgets)."""
    if compact:
        return package_day_breakdown_html(detail)
    nav = (
        nav_chip_row_html([("Summary", True)]) if include_nav else ""
    )
    good_to_know = (
        f'<div class="pkg-info-block">'
        f"<p><strong>Ideal for</strong><br>{html.escape(detail.ideal_for)}</p>"
        f"<p><strong>Cancellation</strong><br>{html.escape(detail.cancellation_hint)}</p>"
        f"<p><strong>Contact</strong><br>{html.escape(detail.operator_contact)}</p>"
        f"</div>"
    )
    section_cards = "".join(
        [
            _section_card_html("Highlights", package_highlights_html(detail)),
            _section_card_html("Inclusions", package_inclusions_html(detail)),
            _section_card_html("Good to know", good_to_know),
        ]
    )
    return (
        f'<div class="pkg-detail-main-html">'
        f"{nav}"
        f"{package_day_breakdown_html(detail)}"
        f'<section class="pkg-day-breakdown pkg-section-cards">{section_cards}</section>'
        f"</div>"
    )


def package_itinerary_price_spacer_html() -> str:
    """Invisible twin of the day-wise summary bar so the pricing card lines up with day cards."""
    return (
        '<p class="pkg-summary-bar pkg-summary-bar--sync" aria-hidden="true">'
        "Day-wise summary</p>"
    )


def package_pricing_card_html(
    pkg: TravelPackage,
    detail: Optional[PackageDetail],
    *,
    per_person: float,
    total: Optional[float] = None,
    travelers: int = 1,
    fare_label: str = "Standard",
) -> str:
    travelers = max(1, int(travelers))
    price = f"₹{per_person:,.0f}"
    was_row = ""
    if detail and (
        (detail.list_price_per_person and detail.list_price_per_person > per_person)
        or detail.promo_label
    ):
        strike = ""
        if detail.list_price_per_person and detail.list_price_per_person > per_person:
            strike = (
                f'<span class="pkg-price-card__strike">'
                f"₹{detail.list_price_per_person:,.0f}</span>"
            )
        promo = ""
        if detail.promo_label:
            promo = (
                f'<span class="pkg-price-card__tag">{html.escape(detail.promo_label)}</span>'
            )
        was_row = f'<div class="pkg-price-card__was">{strike}{promo}</div>'

    total_line = ""
    if total is not None:
        total_line = (
            f'<p class="pkg-price-card__total">'
            f"Package total ({travelers} traveler{'s' if travelers != 1 else ''}): "
            f"<strong>₹{total:,.0f}</strong></p>"
        )

    tour_type = html.escape(detail.tour_type if detail else "Package tour")
    fare_safe = html.escape(fare_label)

    return (
        f'<aside class="pkg-price-card">'
        f'<p class="pkg-price-card__tour">{tour_type}</p>'
        f'<p class="pkg-price-card__fare-tier">{fare_safe}</p>'
        f"{was_row}"
        f'<p class="pkg-price-card__amount">{price}</p>'
        f'<p class="pkg-price-card__basis">Starting price per traveler</p>'
        f'<p class="pkg-price-card__occ">Single occupancy · private room (demo)</p>'
        f"{total_line}"
        f'<p class="pkg-price-card__note">Fare updates when you change travelers, nights, or tier in the form below.</p>'
        f"</aside>"
    )


def render_package_detail_panel(
    pkg: TravelPackage,
    detail: Optional[PackageDetail],
    *,
    per_person: float,
    total: Optional[float] = None,
    travelers: int = 1,
    fare_label: str = "Standard",
    compact: bool = False,
) -> None:
    """Itinerary summary (left) and pricing card (right), Thomas Cook–style."""
    name = html.escape(pkg.name)
    tagline = html.escape(pkg.tagline)
    badges = package_detail_badges_html(pkg, detail)

    _emit_html(
        f'<div class="pkg-detail-hero">'
        f'<h3 class="pkg-detail-hero__title">{name}</h3>'
        f'<p class="pkg-detail-hero__tagline">{tagline}</p>{badges}</div>'
    )

    if detail and not compact:
        _emit_html(nav_chip_row_html([("Summary", True)]))

    main_col, side_col = st.columns([1.55, 1], gap="medium")

    with main_col:
        if detail:
            _emit_html(
                package_detail_body_html(
                    detail, compact=compact, include_nav=compact
                )
            )
        else:
            _emit_html(
                "<p class='pkg-info-block'>Itinerary details are not available for this package.</p>"
            )

    with side_col:
        rail = package_itinerary_price_spacer_html() if detail and not compact else ""
        _emit_html(
            rail
            + package_pricing_card_html(
                pkg,
                detail,
                per_person=per_person,
                total=total,
                travelers=travelers,
                fare_label=fare_label,
            )
        )


def render_package_pricing_actions(
    *,
    package_id: str,
    catalog_mode: bool = False,
) -> None:
    """Streamlit CTAs beside the HTML pricing card."""
    if catalog_mode:
        col_calc, col_view = st.columns(2)
        with col_calc:
            if st.button(
                "Calculate price",
                type="primary",
                use_container_width=True,
                key=f"pkg_calc_{package_id}_cat",
            ):
                st.session_state["pkg_picked_id"] = package_id
                st.session_state["pkg_focus_calculator"] = True
                st.rerun()
        with col_view:
            if st.button(
                "View details",
                use_container_width=True,
                key=f"pkg_select_{package_id}",
            ):
                st.session_state["pkg_picked_id"] = package_id
                st.rerun()
