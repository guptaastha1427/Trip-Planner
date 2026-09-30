"""
Trip Planner AI Agent — Streamlit entry point.

What: UI for trip inputs, agent runs, map, refinement, and feedback.
Why: Capstone deliverable tying together Gemini tools + OSM + persistence.
How: Session state mirrors data/app_state.json; heavy work in button handlers,
     itinerary/map render outside callbacks so filters don't blank the page.
"""

import copy
import html
import json
from typing import Any, Dict, List, Optional, Set

import streamlit as st

from config import (
    DEFAULT_MODEL,
    FAST_MODE_MAX_STEPS,
    get_gemini_api_key,
    get_user_agent,
    is_wikivoyage_rag_enabled,
)
from services.agent import AgentTraceStep, run_agent
from services.feedback import append_feedback, feedback_stats
from services.map_viz import (
    build_deck,
    collect_points_for_filter,
    render_pydeck_map,
    route_steps_markdown,
)
from services.destination_guide import attach_destination_guide
from services.place_images import enrich_itinerary_with_photos, enrich_travel_hints_photos
from services.weather import attach_weather
from services.persistence import load_app_state, save_app_state
from services.trip_history import (
    append_trip_record,
    get_trip_history_cached,
    history_button_label,
    save_trip_history,
    snapshot_history_entry,
)
from services.ui_animations import inject_ui_animations
from services.ui_components import (
    category_label,
    display_city,
    render_hint_tile,
    render_destination_guide_section,
    render_hint_tiles_row,
    render_itinerary_stop_card,
    render_travel_tips_card,
    render_trip_summary,
    render_weather_section,
    section_heading,
)
from services.trace_view import render_agent_execution_trace
from services.travel_hints import attach_travel_hints
from services.nearby_pois import nearby_alternatives
from services.validation import (
    dedupe_itinerary_pois,
    enrich_itinerary_from_pois,
    itinerary_poi_id_set,
    validate_trip_inputs,
    verify_single_day_unchanged,
)


def hint_card_links(place: Dict[str, Any], kind: str = "hotel") -> List[tuple]:
    """Lazy import — avoids Streamlit hot-reload ImportError on hint_links."""
    from services.hint_links import hint_card_links as _links

    return _links(place, kind)


def _show_refinement_diff(before: Optional[Dict], after: Optional[Dict]) -> None:
    """Human-readable before/after stop names after refine."""
    if not before or not after:
        st.caption("Itinerary was updated.")
        return

    def _stop_names(itin: Dict) -> List[str]:
        names: List[str] = []
        for day in itin.get("days", []):
            for block in ("morning", "afternoon", "evening"):
                for item in day.get(block, []):
                    names.append(str(item.get("name", "Activity")))
        return names

    old_names = _stop_names(before)
    new_names = _stop_names(after)
    if old_names == new_names:
        st.warning(
            "The stop list looks the same. Try a clearer request or a place name "
            "in your destination city."
        )
    else:
        st.markdown("**Before:** " + " → ".join(old_names[:12]))
        st.markdown("**After:** " + " → ".join(new_names[:12]))


def _init_session() -> None:
    """Load persisted state once per browser session."""
    if "bootstrapped" in st.session_state:
        return
    disk = load_app_state()
    st.session_state.bootstrapped = True
    st.session_state.itinerary = disk.get("itinerary")
    st.session_state.tool_state = disk.get("tool_state", {"pois": {}, "chunks": []})
    st.session_state.agent_trace: List[AgentTraceStep] = disk.get("agent_trace", [])
    st.session_state.form_destination = disk.get("form_destination", "")
    st.session_state.form_origin = disk.get("form_origin", "")
    st.session_state.form_days = disk.get("form_days", 3)
    st.session_state.form_pace = disk.get("form_pace", "moderate")
    st.session_state.form_interests = disk.get("form_interests", "museums, food, outdoors")
    st.session_state.form_constraints = disk.get("form_constraints", "")
    st.session_state.last_error = None
    st.session_state.pending_refinement_compare = None
    st.session_state.show_celebration = False


def _mark_dirty() -> None:
    """Coalesce disk writes — one flush per rerun at end of main()."""
    st.session_state["_persist_dirty"] = True


def _flush_persist() -> None:
    """Write itinerary + form fields to data/app_state.json (trip_history from session cache)."""
    save_app_state(
        {
            "itinerary": st.session_state.get("itinerary"),
            "tool_state": st.session_state.get("tool_state"),
            "agent_trace": [
                t.__dict__ if hasattr(t, "__dict__") else t
                for t in st.session_state.get("agent_trace", [])[-80:]
            ],
            "form_destination": st.session_state.form_destination,
            "form_origin": st.session_state.get("form_origin", ""),
            "form_days": st.session_state.form_days,
            "form_pace": st.session_state.form_pace,
            "form_interests": st.session_state.form_interests,
            "form_constraints": st.session_state.form_constraints,
            "trip_history": get_trip_history_cached(),
        }
    )
    st.session_state["_persist_dirty"] = False


def _persist_if_dirty() -> None:
    if st.session_state.get("_persist_dirty"):
        _flush_persist()


def _resolve_gemini_key() -> Optional[str]:
    """Gemini key from `.env` or Streamlit secrets."""
    key = get_gemini_api_key()
    if key:
        return key
    try:
        secret = st.secrets.get("GEMINI_API_KEY", None)
        return str(secret).strip() if secret else None
    except Exception:
        return None


def _parse_interests(text: str) -> List[str]:
    return [p.strip() for p in text.split(",") if p.strip()]


def _apply_history_entry(entry: dict) -> None:
    """Restore a saved trip into the active session (no disk write — instant rerun)."""
    st.session_state.itinerary = copy.deepcopy(entry.get("itinerary"))
    st.session_state.tool_state = copy.deepcopy(
        entry.get("tool_state") or {"pois": {}, "chunks": []}
    )
    st.session_state.form_destination = entry.get("destination", "")
    st.session_state.form_origin = entry.get("origin", "")
    st.session_state.form_days = entry.get("trip_days", 3)
    st.session_state.form_pace = entry.get("pace", "moderate")
    st.session_state.form_interests = entry.get("interests", "")
    st.session_state.form_constraints = entry.get("constraints", "")
    st.session_state.active_history_id = entry.get("id")
    st.session_state.last_error = None


def _render_sidebar_history() -> None:
    """Past trips — click to load into the main view."""
    st.sidebar.header("Trip history")
    trips = get_trip_history_cached()
    if not trips:
        st.sidebar.caption("No saved trips yet. Generate an itinerary to build your history.")
        return

    st.sidebar.caption("Scroll for older trips")
    with st.sidebar.container(height=420, border=False):
        for entry in reversed(trips):
            label = history_button_label(entry)
            if st.button(label, key=f"hist_{entry['id']}", width="stretch"):
                _apply_history_entry(entry)
                st.rerun()

    if st.sidebar.button("Clear trip history", type="secondary", width="stretch"):
        save_trip_history([], persist_disk=False)
        _flush_persist()
        st.rerun()


def _agent_settings() -> Dict[str, Any]:
    """Model and agent options (from config / .env, not shown in sidebar)."""
    if "map_style" not in st.session_state:
        st.session_state.map_style = "light"
    return {
        "api_key": _resolve_gemini_key(),
        "model": DEFAULT_MODEL,
        "fast_mode": True,
        "max_steps": FAST_MODE_MAX_STEPS,
        "rag_enabled": is_wikivoyage_rag_enabled(),
        "map_style": st.session_state.map_style,
    }


def _run_generation(mode: str, user_request: str = "", target_day: Optional[int] = None) -> None:
    """Shared path for generate / refine / single-day flows."""
    settings = st.session_state.get("_sidebar_settings", {})
    api_key = settings.get("api_key") or _resolve_gemini_key()
    ua = get_user_agent()

    ok, msg = validate_trip_inputs(
        st.session_state.form_destination,
        int(st.session_state.form_days),
        st.session_state.form_pace,
        st.session_state.form_interests,
    )
    if not ok:
        st.session_state.last_error = msg
        return
    if not api_key:
        st.session_state.last_error = (
            "Gemini API key missing. Add GEMINI_API_KEY to your `.env` file (see `.env.example`)."
        )
        return
    if not ua:
        st.session_state.last_error = (
            "OSM contact email missing. Add OSM_CONTACT_EMAIL to your `.env` file."
        )
        return

    status = st.empty()

    progress_bar = st.progress(0, text="Starting agent…")

    def progress(line: str) -> None:
        status.info(line)
        if "retry" in line.lower():
            progress_bar.progress(40, text=line[:80])
        elif "tool" in line.lower() or "running" in line.lower():
            progress_bar.progress(65, text=line[:80])
        elif "gemini" in line.lower():
            progress_bar.progress(30, text=line[:80])
        else:
            progress_bar.progress(90, text=line[:80])

    before_itin = st.session_state.itinerary

    spinner_msg = (
        "✨ Applying your refinement…"
        if mode == "refine"
        else "✈️ Agent is planning your trip…"
    )
    with st.spinner(spinner_msg):
        result = run_agent(
            api_key=api_key,
            model=settings.get("model", DEFAULT_MODEL),
            destination=st.session_state.form_destination,
            trip_days=int(st.session_state.form_days),
            pace=st.session_state.form_pace,
            interests=_parse_interests(st.session_state.form_interests),
            constraints=st.session_state.form_constraints,
            user_agent=ua,
            fast_mode=settings.get("fast_mode", False),
            max_steps=settings.get("max_steps"),
            rag_enabled=settings.get("rag_enabled", False),
            mode=mode,
            existing_itinerary=before_itin,
            target_day=target_day,
            user_request=user_request or None,
            initial_tool_state=st.session_state.get("tool_state"),
            on_progress=progress,
        )

    status.empty()
    progress_bar.empty()
    st.session_state.agent_trace = result.trace

    if not result.ok:
        st.session_state.show_celebration = False
        st.session_state.last_error = result.error
        if mode == "refine":
            st.session_state.last_refine_error = result.error
        st.session_state.raw_model_output = result.raw_final_text
        return

    if mode == "single_day" and before_itin and target_day:
        try:
            verify_single_day_unchanged(before_itin, result.itinerary, target_day)
        except ValueError as exc:
            st.session_state.last_error = str(exc)
            st.session_state.raw_model_output = result.raw_final_text
            return
        st.session_state.pending_refinement_compare = {
            "before": before_itin,
            "after": result.itinerary,
            "note": f"Regenerated day {target_day}",
        }

    if mode == "refine" and before_itin:
        st.session_state.pending_refinement_compare = {
            "before": before_itin,
            "after": result.itinerary,
            "note": "Full itinerary refinement",
        }

    st.session_state.itinerary = result.itinerary
    st.session_state.tool_state = result.tool_state
    if mode in ("refine", "single_day"):
        ts = st.session_state.tool_state or {}
        ts.pop("_photos_key", None)
    st.session_state.last_error = None
    st.session_state.raw_model_output = ""
    st.session_state.show_celebration = mode == "generate"
    if mode == "refine":
        st.session_state.refine_success = True
    if mode in ("refine", "single_day", "generate"):
        _mark_dirty()
    if mode == "generate":
        append_trip_record(
            destination=st.session_state.form_destination,
            origin=(st.session_state.get("form_origin") or "").strip(),
            trip_days=int(st.session_state.form_days),
            pace=st.session_state.form_pace,
            interests=st.session_state.form_interests,
            constraints=st.session_state.form_constraints,
            itinerary=result.itinerary,
            tool_state=result.tool_state,
            persist_disk=False,
        )


def _render_beginner_travel_guide(tool_state: Dict[str, Any], trip_days: int = 7) -> None:
    """Source/destination, weather, guide, airports, budget hotels, and map tips."""
    hints = (tool_state or {}).get("travel_hints") or {}
    guide = (tool_state or {}).get("destination_guide")
    weather = (tool_state or {}).get("weather")
    if guide:
        section_heading("Know before you go", "travel")
        render_destination_guide_section(guide)
    if weather is not None or hints:
        section_heading("Weather at destination", "travel-sub")
        render_weather_section(weather)
    if not hints:
        return
    section_heading("Getting there & stays", "travel")
    disclaimer = hints.get("price_disclaimer", "")
    if disclaimer:
        st.caption(disclaimer)

    tiles: List[str] = []
    src = hints.get("source")
    dest = hints.get("destination")
    if src:
        tiles.append(
            render_hint_tile(
                f"Source · {src.get('label', 'Home')}",
                src.get("display_name", ""),
                src.get("price_hint", "") or "Green SRC on map",
                src.get("image_url"),
            )
        )
    if dest:
        tiles.append(
            render_hint_tile(
                f"Destination · {dest.get('label', 'Trip')}",
                dest.get("display_name", ""),
                "Purple DST on map",
                dest.get("image_url"),
            )
        )
    render_hint_tiles_row(tiles)

    tips = hints.get("tips") or []
    if tips:
        render_travel_tips_card(tips)

    budget_hotels = hints.get("budget_hotels") or hints.get("hotels") or []
    section_heading("Hotels & budget stays", "travel-sub")
    if budget_hotels:
        render_hint_tiles_row(
            [
                render_hint_tile(
                    ht.get("name", "Hotel"),
                    f"{ht.get('tourism', 'hotel').replace('_', ' ').title()} · "
                    f"~{ht.get('distance_km', '?')} km",
                    ht.get("price_hint", "") or ht.get("remark", ""),
                    ht.get("image_url"),
                    links=hint_card_links(ht, "hotel"),
                )
                for ht in budget_hotels[:4]
            ]
        )
    else:
        st.caption(
            "No hotels found in OpenStreetMap for this area. "
            "Try Booking.com or Google Maps for stays near your itinerary."
        )

    section_heading("Flights", "travel-sub")
    flight = hints.get("flight_details") or {}
    if flight.get("recommendation"):
        st.info(flight["recommendation"])
    if flight.get("duration_hint"):
        st.caption(flight["duration_hint"])
    if flight.get("fare_hint"):
        st.caption(flight["fare_hint"])
    flight_links: List[str] = []
    gfl = flight.get("google_flights_url") or hints.get("flight_route_search")
    if gfl:
        flight_links.append(f"[Google Flights]({gfl})")
    if flight_links:
        st.markdown(" · ".join(flight_links))
    airports = hints.get("airports") or []
    if airports:
        render_hint_tiles_row(
            [
                render_hint_tile(
                    ap.get("name", "Airport"),
                    (
                        f"{ap.get('iata')} · ~{ap.get('distance_km', '?')} km from center"
                        if ap.get("iata")
                        else f"~{ap.get('distance_km', '?')} km from center"
                    ),
                    ap.get("remark", "") or ap.get("price_hint", "") or "Pink AIR on map",
                    ap.get("image_url"),
                    links=hint_card_links(ap, "flight"),
                )
                for ap in airports[:3]
            ]
        )
    else:
        st.caption("No airport found in OpenStreetMap near this destination.")

    mode_rec = hints.get("mode_recommendation")
    if mode_rec:
        section_heading("Train & bus recommendation", "travel-sub")
        st.info(mode_rec)
        route_links: List[str] = []
        if hints.get("train_route_search"):
            route_links.append(f"[Search trains]({hints['train_route_search']})")
        if hints.get("bus_route_search"):
            route_links.append(f"[Search buses]({hints['bus_route_search']})")
        if route_links:
            st.markdown(" · ".join(route_links))

    trains = hints.get("train_stations") or []
    if trains:
        section_heading("Nearest train stations", "travel-sub")
        render_hint_tiles_row(
            [
                render_hint_tile(
                    stn.get("name", "Station"),
                    f"Rail · ~{stn.get('distance_km', '?')} km from center",
                    stn.get("price_hint", "") or stn.get("remark", ""),
                    stn.get("image_url"),
                    links=hint_card_links(stn, "transit"),
                )
                for stn in trains[:4]
            ]
        )

    buses = hints.get("bus_stations") or []
    if buses:
        section_heading("Nearest bus terminals", "travel-sub")
        render_hint_tiles_row(
            [
                render_hint_tile(
                    stn.get("name", "Bus stand"),
                    f"Bus · ~{stn.get('distance_km', '?')} km from center",
                    stn.get("price_hint", "") or stn.get("remark", ""),
                    stn.get("image_url"),
                    links=hint_card_links(stn, "transit"),
                )
                for stn in buses[:4]
            ]
        )

BLOCK_HEADINGS = {
    "morning": "🌅 Morning",
    "afternoon": "☀️ Afternoon",
    "evening": "🌙 Evening",
}


def _apply_stop_swap(
    day_num: int,
    block: str,
    idx: int,
    new_poi_id: str,
    catalog: Dict[str, dict],
) -> None:
    """Replace one itinerary stop with a nearby catalog POI."""
    poi = catalog.get(new_poi_id)
    if not poi or not st.session_state.get("itinerary"):
        return
    itin = copy.deepcopy(st.session_state.itinerary)
    day = next((d for d in itin.get("days", []) if d.get("day") == day_num), None)
    if not day or block not in day or idx >= len(day.get(block, [])):
        return
    activities = list(day[block])
    activities[idx] = {
        "poi_id": new_poi_id,
        "name": poi.get("name", "Place"),
        "why": "You picked this nearby alternative from suggestions below.",
        "category": poi.get("category", ""),
        "lat": poi.get("lat"),
        "lon": poi.get("lon"),
    }
    day[block] = activities
    itin = enrich_itinerary_from_pois(itin, catalog)
    st.session_state.itinerary = itin
    ts = st.session_state.get("tool_state") or {}
    ts.pop("_photos_key", None)
    st.session_state.tool_state = ts
    _mark_dirty()


def _nearby_swap_button_label(n: Dict[str, Any]) -> str:
    name = str(n.get("name", "Place")).strip()
    dist = n.get("distance_km", "?")
    cat = n.get("category_label", "Place")
    return f"{name}\n{dist} km · {cat}"


def _render_nearby_alternatives(
    item: Dict[str, Any],
    catalog: Dict[str, dict],
    day_num: int,
    block: str,
    idx: int,
    trip_poi_ids: Set[str],
) -> None:
    """Horizontal scroll of tappable cards (Streamlit buttons) to swap this stop."""
    nearby = nearby_alternatives(
        catalog,
        item.get("lat"),
        item.get("lon"),
        exclude_ids=trip_poi_ids,
        radius_km=5.5,
        limit=10,
    )
    if not nearby:
        return
    st.markdown(
        '<p class="ui-nearby-label">Nearby — scroll sideways, tap a card to swap</p>',
        unsafe_allow_html=True,
    )
    row_key = f"nearby_row_{day_num}_{block}_{idx}"
    with st.container(
        horizontal=True,
        wrap=False,
        gap="small",
        width="stretch",
        key=row_key,
    ):
        for n in nearby:
            pid = str(n.get("poi_id", ""))
            place_name = str(n.get("name") or "Place")
            if st.button(
                _nearby_swap_button_label(n),
                key=f"swap_{day_num}_{block}_{idx}_{pid}",
                type="secondary",
                width=268,
                wrap=True,
                help=f"Swap to {place_name}",
            ):
                _apply_stop_swap(day_num, block, idx, pid, catalog)
                st.rerun()


def _render_poi_feedback(
    city_key: str,
    day_num: int,
    block: str,
    idx: int,
    poi_id: str,
) -> None:
    """Feedback row aligned with stop text (same column as title/why)."""
    up_col, down_col = st.columns(2)
    with up_col:
        if st.button(
            "👍 Helpful",
            key=f"up_{day_num}_{block}_{idx}_{poi_id}",
            use_container_width=True,
            type="secondary",
        ):
            append_feedback(city_key, poi_id, "up")
            st.toast("Thanks for the feedback!")
    with down_col:
        if st.button(
            "👎 Not helpful",
            key=f"down_{day_num}_{block}_{idx}_{poi_id}",
            use_container_width=True,
            type="secondary",
        ):
            append_feedback(city_key, poi_id, "down")
            st.toast("Feedback recorded.")


def _render_itinerary(
    itinerary: Dict[str, Any],
    city_key: str,
    catalog: Optional[Dict[str, dict]] = None,
) -> None:
    """Day sections with bordered stop cards; nearby swap and feedback per stop."""
    catalog = catalog or {}
    trip_poi_ids = itinerary_poi_id_set(itinerary)
    stop_counter = 0
    for day in itinerary.get("days", []):
        day_num = day.get("day", 1)
        with st.container(border=True):
            st.markdown(f"#### Day {day_num}")
            for block in ("morning", "afternoon", "evening"):
                block_items = day.get(block, [])
                if not block_items:
                    continue
                st.markdown(f"**{BLOCK_HEADINGS.get(block, block.title())}**")
                for idx, item in enumerate(block_items):
                    stop_counter += 1
                    name = item.get("name", "Activity")
                    cat = category_label(item.get("category"))
                    pid = item.get("poi_id", "")

                    def _stop_body(
                        _item=item,
                        _day_num=day_num,
                        _block=block,
                        _idx=idx,
                        _trip_poi_ids=trip_poi_ids,
                        _pid=str(pid),
                    ) -> None:
                        if catalog:
                            _render_nearby_alternatives(
                                _item,
                                catalog,
                                _day_num,
                                _block,
                                _idx,
                                _trip_poi_ids,
                            )
                        _render_poi_feedback(
                            city_key, _day_num, _block, _idx, _pid
                        )

                    render_itinerary_stop_card(
                        stop_counter,
                        name,
                        cat,
                        item.get("why"),
                        item.get("image_url"),
                        body_extra=_stop_body,
                    )


def _render_route_map(
    itinerary: Dict[str, Any],
    tool_state: Dict[str, Any],
) -> None:
    """Interactive PyDeck route map (Map tab)."""
    section_heading("Route map", "map")
    st.caption(
        "Tilted 3D route · hover a dot for photo · "
        "Green = start · Purple = destination · Pink = airport"
    )
    m1, m2 = st.columns([2, 1])
    with m1:
        day_options = ["all"] + [
            f"Day {d.get('day')}" for d in itinerary.get("days", [])
        ]
        day_filter = st.selectbox("Filter by day", day_options, key="map_day_filter")
    with m2:
        st.radio("Theme", ["light", "dark"], horizontal=True, key="map_style")
    deck = build_deck(
        itinerary,
        day_filter=day_filter,
        map_style=st.session_state.get("map_style", "light"),
        travel_hints=(tool_state or {}).get("travel_hints"),
    )
    if deck:
        map_style = st.session_state.get("map_style", "light")
        chart_key = f"trip_route_map_{day_filter.replace(' ', '_')}_{map_style}"
        render_pydeck_map(st, deck, chart_key)
        route_pts = collect_points_for_filter(itinerary, day_filter)
        steps = route_steps_markdown(route_pts)
        if steps:
            with st.expander("Turn-by-turn order"):
                for line in steps:
                    st.markdown(line)
    else:
        st.info("Map will appear when stops have location data.")


def main() -> None:
    st.set_page_config(page_title="Trip Planner AI Agent", layout="wide")
    inject_ui_animations()
    _init_session()
    if st.session_state.get("show_celebration"):
        st.balloons()
        st.session_state.show_celebration = False
    _render_sidebar_history()
    settings = _agent_settings()
    st.session_state._sidebar_settings = settings

    if not _resolve_gemini_key() or not get_user_agent():
        st.warning(
            "Add **GEMINI_API_KEY** and **OSM_CONTACT_EMAIL** to the `.env` file in this "
            "project folder (see `.env.example`), **save the file**, then refresh this page."
        )

    dest_label = display_city(st.session_state.get("form_destination") or "")
    st.title("Trip Planner")
    st.caption(
        "Real places from OpenStreetMap · AI-built day plans · swap nearby stops anytime"
    )
    if dest_label:
        st.markdown(f"**Planning for:** {html.escape(dest_label)}")

    with st.container(border=True):
        section_heading("Plan your trip", "plan")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.text_input("From", key="form_origin", placeholder="Mumbai")
        with c2:
            st.text_input("To", key="form_destination", placeholder="Goa")
        with c3:
            st.number_input("Days", min_value=1, max_value=14, key="form_days")
        r1, r2 = st.columns(2)
        with r1:
            st.selectbox("Schedule", ["relaxed", "moderate", "packed"], key="form_pace")
        with r2:
            st.text_input(
                "Interests",
                key="form_interests",
                placeholder="history, food, outdoors",
            )
        st.text_area(
            "Notes",
            key="form_constraints",
            placeholder="Diet, budget, accessibility…",
            height=72,
        )
        if st.button("Create my itinerary", type="primary", use_container_width=True):
            _run_generation("generate")

    if st.session_state.get("last_error"):
        st.error(st.session_state.last_error)

    itinerary = st.session_state.get("itinerary")

    # Render itinerary + map OUTSIDE button handlers (capstone requirement)
    if itinerary:
        _, dup_removed = dedupe_itinerary_pois(itinerary)
        if dup_removed:
            _mark_dirty()
        city_key = (
            (st.session_state.tool_state or {}).get("city_meta", {}) or {}
        ).get("city_key") or st.session_state.form_destination.lower()

        tool_state = st.session_state.tool_state or {}
        ua = get_user_agent()
        origin = (st.session_state.get("form_origin") or "").strip()
        dest = (st.session_state.form_destination or "").strip()
        tool_state["origin_city"] = origin
        hints_key = f"v5|{origin}|{dest}"
        weather_key = f"{dest.strip().lower()}|{int(st.session_state.get('form_days') or 7)}"
        guide_key = dest.strip().lower()
        has_cached_hints = (
            tool_state.get("_hints_key") == hints_key
            and bool(tool_state.get("travel_hints"))
        )
        has_cached_guide = (
            tool_state.get("_guide_key") == guide_key
            and bool(tool_state.get("destination_guide"))
        )
        has_cached_weather = (
            tool_state.get("_weather_key") == weather_key
            and bool(tool_state.get("weather"))
        )
        if ua and dest.strip() and not has_cached_hints:
            try:
                attach_travel_hints(tool_state, dest, ua)
                tool_state["_hints_key"] = hints_key
                _mark_dirty()
            except Exception as exc:
                st.warning(f"Could not load travel hints: {exc}")
        hints = tool_state.get("travel_hints") or {}
        if ua and hints and tool_state.get("_photos_key") != hints_key:
            try:
                enrich_itinerary_with_photos(
                    itinerary,
                    hints.get("city_label", dest) or dest,
                    ua,
                )
                enrich_travel_hints_photos(hints, ua)
                tool_state["travel_hints"] = hints
                tool_state["_photos_key"] = hints_key
                _mark_dirty()
            except Exception:
                pass
        st.session_state.tool_state = tool_state

        render_trip_summary(itinerary, st.session_state.form_destination)

        tab_plan, tab_map, tab_travel = st.tabs(
            ["Itinerary", "Map", "Travel & stays"]
        )

        poi_catalog = (st.session_state.tool_state or {}).get("pois") or {}

        with tab_plan:
            section_heading("Your itinerary", "itinerary")
            _render_itinerary(itinerary, city_key, catalog=poi_catalog)
            with st.expander("Change one day only"):
                day_num = st.number_input(
                    "Day number",
                    min_value=1,
                    max_value=len(itinerary.get("days", [])) or 1,
                    value=1,
                    key="regen_day",
                )
                single_req = st.text_input(
                    "What should change?",
                    placeholder="More outdoors on this day, swap dinner spot…",
                    key="single_day_request",
                )
                if st.button("Update this day", use_container_width=True):
                    if single_req.strip():
                        _run_generation(
                            "single_day",
                            user_request=single_req.strip(),
                            target_day=int(day_num),
                        )
                        st.rerun()
                    else:
                        st.warning("Describe the change you want for that day.")

        with tab_map:
            _render_route_map(itinerary, tool_state)

        with tab_travel:
            trip_days = int(st.session_state.get("form_days") or 7)
            if ua and dest.strip() and not has_cached_guide:
                try:
                    attach_destination_guide(tool_state, dest, ua)
                    tool_state["_guide_key"] = guide_key
                    _mark_dirty()
                except Exception as exc:
                    st.warning(f"Could not load destination guide: {exc}")
            if dest.strip() and not has_cached_weather:
                try:
                    attach_weather(tool_state, dest, trip_days=trip_days)
                    tool_state["_weather_key"] = weather_key
                    _mark_dirty()
                except Exception:
                    pass
            st.session_state.tool_state = tool_state
            hid = st.session_state.get("active_history_id")
            snap_sig = f"{hid}|{hints_key}|{weather_key}|{guide_key}"
            if hid and st.session_state.get("_history_snap_sig") != snap_sig:
                snapshot_history_entry(
                    hid,
                    itinerary=itinerary,
                    tool_state=tool_state,
                    destination=dest,
                    origin=origin,
                    trip_days=trip_days,
                    pace=st.session_state.form_pace,
                    interests=st.session_state.form_interests,
                    constraints=st.session_state.form_constraints,
                    persist_disk=False,
                )
                st.session_state._history_snap_sig = snap_sig
                _mark_dirty()
            _render_beginner_travel_guide(tool_state, trip_days=trip_days)

        with st.expander("Export & advanced"):
            st.download_button(
                "Download trip (JSON)",
                data=json.dumps(itinerary, indent=2),
                file_name="itinerary.json",
                mime="application/json",
            )
            stats = feedback_stats(city_key)
            if stats:
                st.json(stats)
            raw = st.session_state.get("raw_model_output") or ""
            if raw:
                st.code(raw, language="json")

    render_agent_execution_trace(st.session_state.get("agent_trace"))

    _persist_if_dirty()


if __name__ == "__main__":
    main()
