"""Filter obsolete agent trace steps from UI and persistence."""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

_REMOVED_TRACE_KINDS = frozenset({"crew"})
_REMOVED_TRACE_STEP_NAMES = frozenset(
    {
        "crew_start",
        "crew_kickoff",
        "crew_kickoff_complete",
        "crew_pipeline",
        "poi_researcher",
        "itinerary_planner",
        "grounding_critic",
    }
)


def _normalize_step(item: Any) -> Tuple[int, str, str, str, float]:
    if isinstance(item, dict):
        return (
            int(item.get("step") or 0),
            str(item.get("kind") or ""),
            str(item.get("name") or ""),
            str(item.get("detail") or ""),
            float(item.get("duration_ms") or 0),
        )
    return (
        int(getattr(item, "step", 0) or 0),
        str(getattr(item, "kind", "")),
        str(getattr(item, "name", "")),
        str(getattr(item, "detail", "")),
        float(getattr(item, "duration_ms", 0) or 0),
    )


def sanitize_agent_trace(trace: Optional[List[Any]]) -> List[Any]:
    """Drop removed-pipeline steps so only the Gemini planner trace is shown."""
    out: List[Any] = []
    for item in trace or []:
        _, kind, name, _, _ = _normalize_step(item)
        if kind in _REMOVED_TRACE_KINDS:
            continue
        if name in _REMOVED_TRACE_STEP_NAMES or name.startswith("crew_"):
            continue
        out.append(item)
    return out
