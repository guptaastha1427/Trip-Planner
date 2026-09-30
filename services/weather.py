"""
Destination weather via Open-Meteo (free, no API key).

What: Current conditions + short daily forecast for trip planning.
Why: Helps travelers pack and pick activities without a paid weather API.
How: Lat/lon from tool_state geocode; cached fetch stored under tool_state["weather"].
"""

from typing import Any, Dict, List, Optional

import streamlit as st

from services.http_client import get_json

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes (Open-Meteo)
_WEATHER_LABELS: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


def weather_code_label(code: Optional[int]) -> str:
    if code is None:
        return "Unknown"
    return _WEATHER_LABELS.get(int(code), "Mixed conditions")


def weather_code_icon(code: Optional[int]) -> str:
    c = int(code) if code is not None else -1
    if c in (0, 1):
        return "☀️"
    if c == 2:
        return "⛅"
    if c == 3:
        return "☁️"
    if c in (45, 48):
        return "🌫️"
    if c in (51, 53, 55, 61, 63, 65, 80, 81, 82):
        return "🌧️"
    if c in (71, 73, 75):
        return "❄️"
    if c >= 95:
        return "⛈️"
    return "🌤️"


@st.cache_data(ttl=1800, show_spinner=False)
def _fetch_forecast(lat: float, lon: float, forecast_days: int) -> Optional[Dict[str, Any]]:
    days = max(1, min(int(forecast_days), 14))
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "timezone": "auto",
        "forecast_days": days,
    }
    try:
        return get_json(OPEN_METEO_FORECAST, "trip-planner-weather/1.0", params=params)
    except Exception:
        return None


def _coords_from_tool_state(tool_state: Dict[str, Any]) -> Optional[tuple]:
    hints = tool_state.get("travel_hints") or {}
    dest = hints.get("destination") or {}
    if dest.get("lat") is not None and dest.get("lon") is not None:
        return float(dest["lat"]), float(dest["lon"])
    geo = tool_state.get("city_meta") or {}
    if geo.get("lat") is not None and geo.get("lon") is not None:
        return float(geo["lat"]), float(geo["lon"])
    return None


def _normalize_forecast(raw: Dict[str, Any], trip_days: int) -> Dict[str, Any]:
    current = raw.get("current") or {}
    daily = raw.get("daily") or {}
    dates: List[str] = list(daily.get("time") or [])
    n = min(len(dates), trip_days)
    days_out: List[Dict[str, Any]] = []
    for i in range(n):
        code = (daily.get("weather_code") or [None])[i]
        days_out.append(
            {
                "date": dates[i],
                "temp_max": (daily.get("temperature_2m_max") or [None])[i],
                "temp_min": (daily.get("temperature_2m_min") or [None])[i],
                "precip_prob": (daily.get("precipitation_probability_max") or [None])[i],
                "weather_code": code,
                "label": weather_code_label(code),
                "icon": weather_code_icon(code),
            }
        )
    cur_code = current.get("weather_code")
    return {
        "timezone": raw.get("timezone", ""),
        "current": {
            "temp": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
            "weather_code": cur_code,
            "label": weather_code_label(cur_code),
            "icon": weather_code_icon(cur_code),
        },
        "daily": days_out,
        "summary_line": _summary_line(days_out, cur_code, current.get("temperature_2m")),
    }


def _summary_line(
    days: List[Dict[str, Any]],
    current_code: Optional[int],
    current_temp: Optional[float],
) -> str:
    if current_temp is not None:
        head = (
            f"Now: {weather_code_icon(current_code)} "
            f"{round(current_temp)}°C · {weather_code_label(current_code)}"
        )
    else:
        head = "Forecast for your destination"
    if not days:
        return head
    highs = [d["temp_max"] for d in days if d.get("temp_max") is not None]
    lows = [d["temp_min"] for d in days if d.get("temp_min") is not None]
    if highs and lows:
        return (
            f"{head} · Next {len(days)} day(s): "
            f"roughly {round(min(lows))}–{round(max(highs))}°C"
        )
    return head


def fetch_weather_for_destination(
    lat: float,
    lon: float,
    *,
    trip_days: int = 7,
) -> Optional[Dict[str, Any]]:
    raw = _fetch_forecast(lat, lon, trip_days)
    if not raw:
        return None
    return _normalize_forecast(raw, trip_days)


def attach_weather(
    tool_state: Dict[str, Any],
    destination: str,
    *,
    trip_days: int = 7,
) -> None:
    """Populate tool_state['weather'] when coordinates are known."""
    dest_key = (destination or "").strip().lower()
    cache_key = f"{dest_key}|{int(trip_days)}"
    if tool_state.get("_weather_key") == cache_key and tool_state.get("weather"):
        return

    coords = _coords_from_tool_state(tool_state)
    if not coords:
        tool_state["weather"] = None
        tool_state["_weather_key"] = cache_key
        return

    lat, lon = coords
    weather = fetch_weather_for_destination(lat, lon, trip_days=trip_days)
    tool_state["weather"] = weather
    tool_state["_weather_key"] = cache_key
