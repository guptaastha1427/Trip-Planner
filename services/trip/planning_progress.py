"""
Shared planning-step labels for Trip Planner transparency (Gemini agent + Crew).

What: Uniform "Step N/M · Label — message" progress lines and trace summary stages.
Why: Users see the same planning transparency for crew and default agent paths.
How: emit() for on_progress callbacks; stage defs for trace_view summaries.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence, Tuple

# (trace step names…), title, blurb
GEMINI_PLANNING_STAGES: List[Tuple[Tuple[str, ...], str, str]] = [
    (("agent_start", "fast_fallback"), "Planner setup", "Trip mode and agent options"),
    (("poi_search_start", "search_pois"), "OpenStreetMap POIs", "Geocode city and fetch real places"),
    (("retrieve_guides",), "Wikivoyage guides", "Optional destination context (when enabled)"),
    (
        ("fast_generate", "generate_content", "final", "fast_refine"),
        "Gemini planning",
        "Draft or update itinerary JSON",
    ),
    (
        ("parse_validate", "enrich_itinerary", "parse_retry", "grounding_critic"),
        "Validation & grounding",
        "JSON checks, poi_ids, map coordinates",
    ),
    (("surgical_refine",), "Quick local edit", "Change a stop without full replan"),
    (("travel_hints",), "Travel hints", "Airports, hotels, and practical tips"),
    (("complete",), "Complete", "Itinerary ready to display"),
]

GENERATE_STEP_TOTAL = 5
REFINE_STEP_TOTAL = 4
SINGLE_DAY_STEP_TOTAL = 5
TOOL_AGENT_STEP_TOTAL = 6


def emit(
    on_progress: Optional[Callable[[str], None]],
    step: int,
    total: int,
    label: str,
    message: str,
) -> None:
    if on_progress:
        on_progress(f"Step {step}/{total} · {label} — {message}")


def stage_status_from_trace(
    trace: Sequence[object],
    names: Tuple[str, ...],
) -> Tuple[str, str, str]:
    """
    Map trace rows matching any of `names` to (status label, detail, duration str).
    """
    rows = []
    for item in trace:
        if isinstance(item, dict):
            name = str(item.get("name") or "")
            detail = str(item.get("detail") or "")
            ms = float(item.get("duration_ms") or 0)
            kind = str(item.get("kind") or "")
        else:
            name = str(getattr(item, "name", ""))
            detail = str(getattr(item, "detail", ""))
            ms = float(getattr(item, "duration_ms", 0) or 0)
            kind = str(getattr(item, "kind", ""))
        if name in names:
            rows.append((name, kind, detail, ms))
    if not rows:
        return ("⏸ Not run", "—", "")
    last_name, kind, detail, ms = rows[-1]
    dur = _format_duration(ms)
    if any(x in detail.lower() for x in ("fail", "error", "invalid")) and "passed" not in detail.lower():
        return ("❌ Failed", detail, dur)
    if name in ("parse_validate", "enrich_itinerary", "grounding_critic") and detail:
        if "passed" in detail.lower() or "checks passed" in detail.lower():
            return ("✅ Passed", detail, dur)
    if len(rows) > 1 and name in ("fast_generate", "generate_content", "itinerary_planner"):
        return (f"✅ Done ({len(rows)} steps)", detail, dur)
    if name == "complete" or kind == "postprocess":
        return ("✅ Done", detail, dur)
    return ("✅ Done", detail or last_name.replace("_", " "), dur)


def _format_duration(ms: float) -> str:
    if ms <= 0:
        return ""
    if ms < 1000:
        return f"{ms:.0f} ms"
    return f"{ms / 1000:.1f} s"
