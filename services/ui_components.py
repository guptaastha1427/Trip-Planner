"""UI helpers — self-contained HTML only (no open/close wrappers around widgets)."""

import html
from typing import Any, Callable, Dict, List, Optional

import streamlit as st

from services.hint_links import hotel_hint_links, transport_hint_links

__all__ = [
    "section_heading",
    "render_trip_summary",
    "render_hint_tiles_row",
    "render_hint_tile",
    "render_travel_tips_card",
    "render_destination_guide_section",
    "render_weather_section",
    "render_stop_media",
    "render_itinerary_stop_card",
    "render_compact_stop_card",
    "category_label",
    "display_city",
    "hotel_hint_links",
    "transport_hint_links",
]


def display_city(label: str) -> str:
    s = (label or "").strip()
    if not s:
        return s
    return s.title() if s.islower() else s


def _plain_tip_text(text: str) -> str:
    return str(text).replace("***", "").replace("**", "")


_SECTION_VARIANTS = frozenset(
    {"travel", "travel-sub", "itinerary", "day", "block", "refine", "map", "plan"}
)


def section_heading(title: str, variant: str = "itinerary") -> None:
    key = variant if variant in _SECTION_VARIANTS else "itinerary"
    safe = html.escape(str(title))
    st.markdown(
        f'<p class="trip-h trip-h--{key}">{safe}</p>',
        unsafe_allow_html=True,
    )


def render_trip_summary(itinerary: Dict[str, Any], destination: str) -> None:
    days = len(itinerary.get("days", []))
    stops = sum(
        len(day.get(b, []))
        for day in itinerary.get("days", [])
        for b in ("morning", "afternoon", "evening")
    )
    dest = html.escape(
        display_city(destination or itinerary.get("destination", "Your trip") or "")
        or "Your trip"
    )
    st.markdown(
        f"""
        <div class="trip-stats">
            <div class="trip-stats__cell"><strong>{dest}</strong><span>Destination</span></div>
            <div class="trip-stats__cell"><strong>{days}</strong><span>Days</span></div>
            <div class="trip-stats__cell"><strong>{stops}</strong><span>Stops</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hint_tiles_row(tiles_html: List[str]) -> None:
    if not tiles_html:
        return
    st.markdown(
        f'<div class="hint-scroll">{"".join(tiles_html)}</div>',
        unsafe_allow_html=True,
    )


def render_hint_tile(
    title: str,
    subtitle: str,
    meta: str,
    image_url: Optional[str],
    links: Optional[List[tuple]] = None,
) -> str:
    if image_url:
        media = (
            f'<img class="hint-card__img" src="{html.escape(image_url)}" alt="" '
            f'loading="lazy" />'
        )
    else:
        media = '<div class="hint-card__placeholder" aria-hidden="true"></div>'
    body = (
        f'<article class="hint-card">'
        f'<div class="hint-card__media">{media}</div>'
        f'<div class="hint-card__body">'
        f'<h4 class="hint-card__title">{html.escape(str(title or ""))}</h4>'
        f'<p class="hint-card__sub">{html.escape(str(subtitle or ""))}</p>'
        f'<p class="hint-card__meta">{html.escape(str(meta or ""))}</p>'
    )
    if links:
        link_bits = []
        for label, href in links:
            if not href:
                continue
            link_bits.append(
                f'<a class="hint-card__link" href="{html.escape(str(href))}" '
                f'target="_blank" rel="noopener noreferrer">'
                f"{html.escape(str(label))}</a>"
            )
        if link_bits:
            body += f'<p class="hint-card__links">{"".join(link_bits)}</p>'
    return body + "</div></article>"


def render_stop_media(image_url: Optional[str]) -> None:
    """Itinerary stop image or gradient placeholder (Streamlit-safe)."""
    if image_url:
        st.image(image_url, use_container_width=True)
    else:
        st.markdown(
            '<div class="stop-card__placeholder" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )


def render_itinerary_stop_card(
    stop_num: int,
    name: str,
    category: str,
    why: Optional[str],
    image_url: Optional[str],
    body_extra: Optional[Callable[[], None]] = None,
) -> None:
    """Itinerary stop — bordered container, image column + text/widgets column."""
    with st.container(border=True):
        img_col, body_col = st.columns([1, 2.4])
        with img_col:
            render_stop_media(image_url)
        with body_col:
            st.markdown(f"**{stop_num}. {name or 'Activity'}**")
            st.caption(category or "Place")
            if why:
                st.write(why)
            if body_extra:
                body_extra()


def render_compact_stop_card(
    stop_num: int,
    name: str,
    category: str,
    why: Optional[str],
    image_url: Optional[str],
) -> None:
    """Alias for itinerary row card (kept for imports)."""
    render_itinerary_stop_card(stop_num, name, category, why, image_url)


def render_destination_guide_section(guide: Dict[str, Any]) -> None:
    if not guide:
        return
    city = html.escape(display_city(guide.get("city_label", "") or "Destination"))
    about = html.escape(str(guide.get("about", "")))
    best = html.escape(str(guide.get("best_seasons", "")))
    avoid = html.escape(str(guide.get("avoid_seasons", "")))
    tip = html.escape(str(guide.get("season_tip", "")))
    st.markdown(
        f"""
        <div class="dest-guide-card">
            <h4 class="dest-guide-card__title">About {city}</h4>
            <p class="dest-guide-card__about">{about}</p>
            <div class="dest-guide-card__grid">
                <div class="dest-guide-card__cell dest-guide-card__cell--good">
                    <span class="dest-guide-card__label">Best time to visit</span>
                    <p>{best}</p>
                </div>
                <div class="dest-guide-card__cell dest-guide-card__cell--avoid">
                    <span class="dest-guide-card__label">Consider avoiding</span>
                    <p>{avoid}</p>
                </div>
            </div>
            {f'<p class="dest-guide-card__tip">{tip}</p>' if tip else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_weather_section(weather: Optional[Dict[str, Any]]) -> None:
    if not weather:
        st.caption("Weather unavailable — destination coordinates missing or forecast API busy.")
        return
    current = weather.get("current") or {}
    summary = html.escape(str(weather.get("summary_line", "")))
    cur_line = ""
    if current.get("temp") is not None:
        icon = html.escape(str(current.get("icon", "")))
        label = html.escape(str(current.get("label", "")))
        temp = round(float(current["temp"]))
        hum = current.get("humidity")
        hum_bit = f" · {int(hum)}% humidity" if hum is not None else ""
        cur_line = f"{icon} <strong>{temp}°C</strong> {label}{hum_bit}"
    daily = weather.get("daily") or []
    chips = []
    for day in daily[:7]:
        d_label = html.escape(str(day.get("date", ""))[-5:] or "")
        icon = html.escape(str(day.get("icon", "")))
        tmax = day.get("temp_max")
        tmin = day.get("temp_min")
        if tmax is not None and tmin is not None:
            temps = f"{round(tmin)}–{round(tmax)}°C"
        else:
            temps = ""
        chips.append(
            f'<div class="weather-chip"><span class="weather-chip__date">{d_label}</span>'
            f'<span class="weather-chip__icon">{icon}</span>'
            f'<span class="weather-chip__temp">{html.escape(temps)}</span></div>'
        )
    chip_html = "".join(chips)
    st.markdown(
        f"""
        <div class="weather-card">
            <p class="weather-card__summary">{summary}</p>
            {f'<p class="weather-card__now">{cur_line}</p>' if cur_line else ''}
            <div class="weather-chip-row">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_travel_tips_card(tips: List[str]) -> None:
    if not tips:
        return
    items = "".join(
        f'<li class="travel-tips-card__item">{html.escape(_plain_tip_text(t))}</li>'
        for t in tips
    )
    st.markdown(
        f'<div class="travel-tips-card"><ul class="travel-tips-card__list">{items}</ul></div>',
        unsafe_allow_html=True,
    )


def category_label(raw: Optional[str]) -> str:
    if not raw:
        return "Place"
    text = str(raw).replace("_", " ")
    if "=" in text:
        text = text.split("=", 1)[-1]
    return text.replace("|", " · ").title()[:36]
