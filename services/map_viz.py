"""
PyDeck map per capstone .docs: ScatterplotLayer + PathLayer, tooltips, day filter.

Built with native pydeck layers so TextLayer labels render in Streamlit.
Avoids mapStyle URLs that break deck.gl parse errors in the browser.
"""

import json
import math
from typing import Any, Dict, List, Optional

import pandas as pd
import pydeck as pdk

BLOCK_LABELS = {
    "morning": "Morning",
    "afternoon": "Afternoon",
    "evening": "Evening",
}

_MAP_PITCH = 52
_MAP_BEARING = -18
_ARC_HEIGHT = 7
_ROUTE_TOOLTIP_HTML = (
    "<div class='trip-map-tooltip' style='padding:12px 14px;background:#fff;"
    "color:#334155;font-family:Plus Jakarta Sans,system-ui,sans-serif;"
    "font-size:13px;line-height:1.45;'>"
    "<div style='font-size:14px;font-weight:700;color:#0f172a;margin-bottom:4px;'>"
    "{stop_num}: {name}</div>"
    "<div style='font-size:12px;font-weight:500;color:#475569;'>{category}</div>"
    "<div style='font-size:12px;font-style:italic;color:#64748b;margin-top:4px;'>"
    "{day_block}</div>"
    "<div style='font-size:12px;color:#334155;margin-top:6px;'>{route_hint}</div>"
    "<img src='{image_url}' alt='' style='display:block;width:100%;max-width:220px;"
    "border-radius:8px;margin-top:8px;' onerror=\"this.style.display='none'\"/>"
    "</div>"
)

# deck.gl defaults to a dark tooltip shell; style overrides the popup container.
_ROUTE_TOOLTIP_STYLE: Dict[str, str] = {
    "backgroundColor": "#ffffff",
    "color": "#0f172a",
    "border": "1px solid #cbd5e1",
    "borderRadius": "12px",
    "boxShadow": "0 12px 32px rgba(15, 23, 42, 0.2)",
    "padding": "0",
    "fontSize": "13px",
    "fontFamily": '"Plus Jakarta Sans", system-ui, sans-serif',
    "maxWidth": "280px",
    "lineHeight": "1.45",
    "zIndex": "9999",
    "pointerEvents": "none",
}


def route_map_tooltip() -> Dict[str, Any]:
    """Tooltip config for PyDeck / deck.gl (html + light container style)."""
    return {"html": _ROUTE_TOOLTIP_HTML, "style": dict(_ROUTE_TOOLTIP_STYLE)}


MAP_THEMES: Dict[str, Dict[str, Any]] = {
    "light": {
        "scatter": [59, 130, 246, 240],
        "scatter_line": [30, 64, 175, 255],
        "path": [249, 115, 22, 235],
        "path_shadow": [154, 52, 18, 160],
        "path_glow": [253, 186, 116, 100],
        "arc_source": [251, 146, 60, 230],
        "arc_target": [234, 88, 12, 255],
        "arrow": [194, 65, 12, 255],
        "badge_bg": [30, 64, 175, 255],
        "badge_text": [255, 255, 255, 255],
        "name_bg": [255, 255, 255, 235],
        "name_text": [15, 23, 42, 255],
        "canvas": [248, 250, 252, 255],
    },
    "dark": {
        "scatter": [56, 189, 248, 255],
        "scatter_line": [248, 250, 252, 230],
        "path": [251, 191, 36, 240],
        "path_shadow": [120, 53, 15, 170],
        "path_glow": [254, 243, 199, 90],
        "arc_source": [253, 224, 71, 240],
        "arc_target": [245, 158, 11, 255],
        "arrow": [254, 243, 199, 255],
        "badge_bg": [14, 116, 144, 255],
        "badge_text": [255, 255, 255, 255],
        "name_bg": [15, 23, 42, 230],
        "name_text": [248, 250, 252, 255],
        "canvas": [15, 23, 42, 255],
    },
}

_ARROW_CHAR = "\u25b6"  # ▶
_ARROW_FRACTIONS = (0.28, 0.5, 0.72)
_ENDPOINT_BADGE = {"source": "SRC", "destination": "DST", "airport": "AIR"}
_ENDPOINT_FILL: Dict[str, List[int]] = {
    "source": [34, 197, 94, 240],
    "destination": [168, 85, 247, 240],
    "airport": [236, 72, 153, 240],
}
_CONNECTOR_COLOR = [100, 116, 139, 180]
_MAX_ENDPOINT_KM = 150.0


def _attach_map_labels(points: List[dict]) -> None:
    for pt in points:
        name = str(pt.get("name") or "POI")
        if len(name) > 26:
            name = name[:23] + "..."
        pt["stop_badge"] = str(pt["stop_num"])
        pt["name_line"] = name


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _endpoint_markers(travel_hints: Optional[Dict[str, Any]], stops: List[dict]) -> List[dict]:
    if not travel_hints or not stops:
        return []
    center_lat = sum(s["lat"] for s in stops) / len(stops)
    center_lon = sum(s["lon"] for s in stops) / len(stops)
    markers: List[dict] = []

    def _maybe_add(ep: Optional[dict], role: str) -> None:
        if not ep or ep.get("lat") is None or ep.get("lon") is None:
            return
        lat, lon = float(ep["lat"]), float(ep["lon"])
        if role == "source" and _haversine_km(center_lat, center_lon, lat, lon) > _MAX_ENDPOINT_KM:
            return
        label = ep.get("label") or ep.get("name") or role.title()
        markers.append(
            {
                "lat": lat,
                "lon": lon,
                "name": label,
                "category": role.title(),
                "day_block": ep.get("display_name", label),
                "route_hint": f"{role.title()} marker",
                "stop_num": _ENDPOINT_BADGE.get(role, role),
                "role": role,
                "stop_badge": _ENDPOINT_BADGE.get(role, role),
                "name_line": label[:26],
                "fill_color": _ENDPOINT_FILL.get(role, [120, 120, 120, 220]),
                "image_url": str(ep.get("image_url") or ""),
            }
        )

    _maybe_add(travel_hints.get("source"), "source")
    _maybe_add(travel_hints.get("destination"), "destination")
    _maybe_add(travel_hints.get("nearest_airport"), "airport")
    return markers


def _connector_routes(endpoints: List[dict], stops: List[dict]) -> List[List[List[float]]]:
    if not stops:
        return []
    by_role = {e["role"]: e for e in endpoints}
    routes: List[List[List[float]]] = []
    src = by_role.get("source")
    air = by_role.get("airport")
    first = stops[0]
    if src and air:
        routes.append(
            [
                [src["lon"], src["lat"]],
                [air["lon"], air["lat"]],
            ]
        )
    if air:
        routes.append(
            [
                [air["lon"], air["lat"]],
                [first["lon"], first["lat"]],
            ]
        )
    return routes


def _collect_points(itinerary: Dict[str, Any], day_filter: str) -> List[dict]:
    points: List[dict] = []
    for day in itinerary.get("days", []):
        day_num = day.get("day")
        label = f"Day {day_num}"
        if day_filter != "all" and day_filter != label:
            continue
        for block in ("morning", "afternoon", "evening"):
            block_label = BLOCK_LABELS.get(block, block.title())
            for item in day.get(block, []):
                lat, lon = item.get("lat"), item.get("lon")
                if lat is None or lon is None:
                    continue
                stop_num = len(points) + 1
                points.append(
                    {
                        "lat": float(lat),
                        "lon": float(lon),
                        "name": item.get("name", "POI"),
                        "category": (item.get("category") or "").replace("=", " "),
                        "day_block": f"{label} · {block_label}",
                        "block": block_label,
                        "stop_num": stop_num,
                        "image_url": str(item.get("image_url") or ""),
                    }
                )
    for i, pt in enumerate(points):
        if i + 1 < len(points):
            nxt = points[i + 1]
            pt["route_hint"] = f"Next stop {nxt['stop_num']} {nxt['name']}"
        else:
            pt["route_hint"] = "Last stop for this view."
    return points


def _view_state(points: List[dict], extra: Optional[List[dict]] = None) -> pdk.ViewState:
    all_pts = list(points) + list(extra or [])
    if not all_pts:
        return pdk.ViewState(latitude=0, longitude=0, zoom=2)
    lats = [p["lat"] for p in all_pts]
    lons = [p["lon"] for p in all_pts]
    spread = max(max(lats) - min(lats), max(lons) - min(lons), 0.02)
    zoom = 11 if spread < 0.05 else 10 if spread < 0.15 else 8
    return pdk.ViewState(
        latitude=sum(lats) / len(lats),
        longitude=sum(lons) / len(lons),
        zoom=zoom,
        pitch=_MAP_PITCH,
        bearing=_MAP_BEARING,
    )


def _bearing_deg(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_lon = math.radians(lon2 - lon1)
    x = math.sin(d_lon) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(d_lon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def _arc_rows(points: List[dict]) -> List[dict]:
    rows: List[dict] = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        rows.append(
            {
                "lon": a["lon"],
                "lat": a["lat"],
                "lon2": b["lon"],
                "lat2": b["lat"],
                "from_name": a["name"],
                "to_name": b["name"],
                "leg_label": f"Stop {a['stop_num']} to Stop {b['stop_num']}",
            }
        )
    return rows


def _arrow_rows(points: List[dict]) -> List[dict]:
    rows: List[dict] = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        bearing = _bearing_deg(a["lon"], a["lat"], b["lon"], b["lat"])
        for frac in _ARROW_FRACTIONS:
            rows.append(
                {
                    "lon": a["lon"] + (b["lon"] - a["lon"]) * frac,
                    "lat": a["lat"] + (b["lat"] - a["lat"]) * frac,
                    "angle": bearing,
                    "arrow": _ARROW_CHAR,
                }
            )
    return rows


def _sanitize_deck_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    spec.pop("mapStyle", None)
    spec.pop("mapProvider", None)
    view = spec.get("initialViewState") or spec.get("viewState")
    if isinstance(view, dict):
        view.setdefault("pitch", _MAP_PITCH)
        view.setdefault("bearing", _MAP_BEARING)
    return spec


def _route_path_layers(
    route: List[List[float]],
    theme: Dict[str, Any],
    *,
    wide: bool = True,
) -> List[pdk.Layer]:
    """Ground shadow + bright cap for a readable 3D-style route."""
    if len(route) < 2:
        return []
    data = [{"route": route}]
    layers: List[pdk.Layer] = []
    if wide:
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=data,
                get_path="route",
                get_color=theme.get("path_shadow", theme["path"]),
                get_width=12,
                width_min_pixels=7,
                joint_rounded=True,
                cap_rounded=True,
                pickable=False,
            )
        )
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=data,
                get_path="route",
                get_color=theme.get("path_glow", theme["path"]),
                get_width=8,
                width_min_pixels=5,
                joint_rounded=True,
                cap_rounded=True,
                pickable=False,
            )
        )
    layers.append(
        pdk.Layer(
            "PathLayer",
            data=data,
            get_path="route",
            get_color=theme["path"],
            get_width=5,
            width_min_pixels=4,
            joint_rounded=True,
            cap_rounded=True,
            pickable=False,
        )
    )
    return layers


def _build_layers(
    points: List[dict],
    map_style: str,
    endpoints: Optional[List[dict]] = None,
) -> List[pdk.Layer]:
    theme = MAP_THEMES.get(map_style, MAP_THEMES["light"])
    endpoints = endpoints or []
    _attach_map_labels(points)
    df = pd.DataFrame(points)

    layers: List[pdk.Layer] = []

    for route in _connector_routes(endpoints, points):
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=[{"route": route}],
                get_path="route",
                get_color=_CONNECTOR_COLOR,
                get_width=4,
                width_min_pixels=2,
                joint_rounded=True,
                cap_rounded=True,
                pickable=False,
            )
        )

    if points:
        main_route = [[p["lon"], p["lat"]] for p in points]
        layers.extend(_route_path_layers(main_route, theme, wide=True))

    arcs = _arc_rows(points)
    if arcs:
        layers.append(
            pdk.Layer(
                "ArcLayer",
                data=arcs,
                get_source_position="[lon, lat]",
                get_target_position="[lon2, lat2]",
                get_source_color=theme["arc_source"],
                get_target_color=theme["arc_target"],
                get_width=5,
                width_min_pixels=4,
                get_height=_ARC_HEIGHT,
                pickable=False,
            )
        )
        layers.append(
            pdk.Layer(
                "TextLayer",
                data=_arrow_rows(points),
                get_position="[lon, lat]",
                get_text="arrow",
                get_angle="angle",
                get_size=22,
                get_color=theme["arrow"],
                pickable=False,
            )
        )

    if endpoints:
        for role, color in _ENDPOINT_FILL.items():
            role_pts = [e for e in endpoints if e.get("role") == role]
            if not role_pts:
                continue
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame(role_pts),
                    get_position="[lon, lat]",
                    get_radius=45,
                    get_fill_color=color,
                    get_line_color=[255, 255, 255, 220],
                    line_width_min_pixels=2,
                    radius_min_pixels=9,
                    radius_max_pixels=18,
                    pickable=True,
                    auto_highlight=True,
                    highlight_color=[255, 255, 255, 200],
                )
            )
        layers.append(
            pdk.Layer(
                "TextLayer",
                data=endpoints,
                get_position="[lon, lat]",
                get_text="stop_badge",
                get_size=14,
                get_color=[255, 255, 255, 255],
                get_background=True,
                get_background_color=[30, 41, 59, 200],
                get_background_padding=[5, 3],
                get_alignment_baseline="center",
                pickable=False,
            )
        )
        layers.append(
            pdk.Layer(
                "TextLayer",
                data=endpoints,
                get_position="[lon, lat]",
                get_text="name_line",
                get_size=12,
                get_color=theme["name_text"],
                get_background=True,
                get_background_color=theme["name_bg"],
                get_background_padding=[4, 2],
                get_pixel_offset=[0, -28],
                get_alignment_baseline="bottom",
                pickable=False,
            )
        )

    if not points:
        return layers

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="[lon, lat]",
            get_radius=52,
            get_fill_color=[15, 23, 42, 50],
            get_line_color=[0, 0, 0, 0],
            radius_min_pixels=11,
            radius_max_pixels=22,
            pickable=False,
        )
    )
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="[lon, lat]",
            get_radius=35,
            get_fill_color=theme["scatter"],
            get_line_color=theme["scatter_line"],
            line_width_min_pixels=2,
            radius_min_pixels=8,
            radius_max_pixels=18,
            pickable=True,
            auto_highlight=True,
            highlight_color=[255, 255, 255, 220],
            stroked=True,
            filled=True,
        )
    )
    layers.append(
        pdk.Layer(
            "TextLayer",
            data=points,
            get_position="[lon, lat]",
            get_text="stop_badge",
            get_size=15,
            get_color=theme["badge_text"],
            get_background=True,
            get_background_color=theme["badge_bg"],
            get_background_padding=[6, 4],
            get_alignment_baseline="center",
            pickable=False,
        )
    )
    layers.append(
        pdk.Layer(
            "TextLayer",
            data=points,
            get_position="[lon, lat]",
            get_text="name_line",
            get_size=13,
            get_color=theme["name_text"],
            get_background=True,
            get_background_color=theme["name_bg"],
            get_background_padding=[5, 3],
            get_pixel_offset=[0, -26],
            get_alignment_baseline="bottom",
            pickable=False,
        )
    )
    return layers


def _build_spec_json(
    points: List[dict],
    view: pdk.ViewState,
    map_style: str = "light",
    endpoints: Optional[List[dict]] = None,
) -> str:
    theme = MAP_THEMES.get(map_style, MAP_THEMES["light"])
    layers = _build_layers(points, map_style, endpoints)
    tooltip = route_map_tooltip()
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view,
        map_style=None,
        tooltip=tooltip,
    )
    spec = json.loads(deck.to_json())
    spec = _sanitize_deck_spec(spec)
    spec["parameters"] = {"clearColor": theme["canvas"]}
    spec["tooltip"] = tooltip
    return json.dumps(spec)


def build_deck(
    itinerary: Optional[Dict[str, Any]],
    day_filter: str = "all",
    map_style: str = "light",
    travel_hints: Optional[Dict[str, Any]] = None,
) -> Optional[pdk.Deck]:
    if not itinerary:
        return None

    points = _collect_points(itinerary, day_filter)
    endpoints = _endpoint_markers(travel_hints, points)
    if not points and not endpoints:
        return None

    view = _view_state(points, endpoints)
    style_key = "dark" if map_style == "dark" else "light"
    spec_json = _build_spec_json(points, view, style_key, endpoints)

    deck = pdk.Deck(layers=[], initial_view_state=view, map_style=None)
    deck._tooltip = route_map_tooltip()
    deck.to_json = lambda: spec_json  # type: ignore[method-assign, assignment]
    return deck


def render_pydeck_map(
    st_module: Any,
    deck: pdk.Deck,
    chart_key: str = "trip_route_map",
) -> None:
    st_module.pydeck_chart(deck, width="stretch", key=chart_key)


show_route_map = render_pydeck_map


def collect_points_for_filter(
    itinerary: Dict[str, Any],
    day_filter: str,
) -> List[dict]:
    return _collect_points(itinerary, day_filter)


def route_steps_markdown(points: List[dict]) -> List[str]:
    lines: List[str] = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        lines.append(
            f"**Stop {a['stop_num']}** ({a['block']}): {a['name']} "
            f"→ **Stop {b['stop_num']}** ({b['block']}): {b['name']}"
        )
    return lines
