"""User-facing display of agent execution trace steps."""

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from services.ui_components import section_heading

# Internal step name -> pipeline phase id
_NAME_TO_PHASE: Dict[str, str] = {
    "agent_start": "start",
    "fast_fallback": "start",
    "poi_search_start": "search",
    "search_pois": "search",
    "retrieve_guides": "guides",
    "generate_content": "ai",
    "fast_generate": "ai",
    "fast_refine": "ai",
    "final": "ai",
    "surgical_refine": "quick_edit",
    "parse_validate": "validate",
    "parse_retry": "validate",
    "enrich_itinerary": "validate",
    "travel_hints": "extras",
    "complete": "done",
}

_PHASES: List[Dict[str, str]] = [
    {
        "id": "start",
        "title": "Starting planner",
        "blurb": "Trip mode, fast path, and agent options are set.",
    },
    {
        "id": "search",
        "title": "Searching places (OpenStreetMap)",
        "blurb": "Geocode the city and fetch real POIs matching your interests.",
    },
    {
        "id": "guides",
        "title": "Loading travel guides (Wikivoyage)",
        "blurb": "Retrieve guide chunks when RAG is enabled.",
    },
    {
        "id": "ai",
        "title": "AI building itinerary",
        "blurb": "Gemini plans days, calls tools, and returns itinerary JSON.",
    },
    {
        "id": "quick_edit",
        "title": "Quick local edit",
        "blurb": "Add or swap a stop without a full replan.",
    },
    {
        "id": "validate",
        "title": "Validating & grounding stops",
        "blurb": "Parse JSON, check poi_ids, and attach map coordinates.",
    },
    {
        "id": "extras",
        "title": "Travel hints",
        "blurb": "Airports, hotels, and practical tips for the destination.",
    },
    {
        "id": "done",
        "title": "Final itinerary",
        "blurb": "Plan is ready to show on the map and day cards.",
    },
]

_STEP_EXPLANATIONS = {
    "agent_start": "Planner run started with your trip settings.",
    "fast_fallback": "Fast one-shot plan failed; continuing with the tool agent.",
    "poi_search_start": "Starting OpenStreetMap POI search.",
    "search_pois": "Fetched places from OpenStreetMap.",
    "retrieve_guides": "Loaded Wikivoyage excerpts for context.",
    "generate_content": "Gemini turn: tool calls or planning.",
    "fast_generate": "Single-shot Gemini draft from the POI catalog.",
    "fast_refine": "Gemini updated the itinerary for your request.",
    "final": "Gemini returned final itinerary JSON.",
    "surgical_refine": "Applied a quick local edit without full replan.",
    "parse_validate": "Parsed JSON and validated structure and poi_ids.",
    "parse_retry": "Asked Gemini to fix invalid JSON or poi_ids.",
    "enrich_itinerary": "Grounded each stop with lat/lon from the POI catalog.",
    "travel_hints": "Loaded airports, hotels, and tips.",
    "complete": "Itinerary ready.",
}

_KIND_LABELS = {
    "agent": "Agent",
    "phase": "Phase",
    "tool": "Tool",
    "model": "Model",
    "validate": "Validate",
    "postprocess": "Post",
    "retry": "Retry",
}


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
        int(item.step),
        str(item.kind),
        str(item.name),
        str(item.detail),
        float(item.duration_ms),
    )


def _phase_for_name(name: str, kind: str) -> str:
    if name in _NAME_TO_PHASE:
        return _NAME_TO_PHASE[name]
    if kind == "retry":
        return "ai"
    if kind == "tool" and name not in _NAME_TO_PHASE:
        return "search"
    if kind == "model":
        return "ai"
    return "start"


def _explain_step(name: str, kind: str, detail: str) -> str:
    base = _STEP_EXPLANATIONS.get(name)
    if base:
        if detail and name in ("search_pois", "retrieve_guides", "poi_search_start"):
            return f"{base} ({detail})."
        if detail and name in ("surgical_refine", "parse_validate", "parse_retry"):
            return f"{base} {detail}."
        if detail and name == "enrich_itinerary":
            return f"{base} {detail}."
        return base
    if kind == "retry":
        if detail:
            return f"Retried Gemini after a temporary error ({detail})."
        return "Retried Gemini after a temporary error."
    label = _KIND_LABELS.get(kind, kind.title() if kind else "Step")
    if detail:
        return f"{label} “{name}”: {detail}."
    return f"{label} “{name}”."


def _format_duration(ms: float) -> str:
    if ms <= 0:
        return ""
    if ms < 1000:
        return f"{ms:.0f} ms"
    return f"{ms / 1000:.1f} s"


def render_agent_execution_trace(trace: Optional[List[Any]]) -> None:
    """Bottom-of-page timeline of agent steps (dict or AgentTraceStep items)."""
    with st.container(border=True):
        section_heading("Debug & agent execution", "refine")
        items = list(trace or [])
        if not items:
            st.caption("Generate an itinerary to see agent steps.")
            return

        normalized = [_normalize_step(t) for t in items]
        total_ms = sum(m for _, _, _, _, m in normalized)

        by_phase: Dict[str, List[Tuple[int, str, str, str, float]]] = defaultdict(list)
        for row in normalized:
            step_num, kind, name, detail, ms = row
            by_phase[_phase_for_name(name, kind)].append(row)

        visible_phases = [p for p in _PHASES if by_phase.get(p["id"])]
        if not visible_phases:
            visible_phases = [_PHASES[0]]

        pipeline_lines: List[str] = []
        for idx, phase in enumerate(visible_phases, start=1):
            steps = by_phase.get(phase["id"], [])
            phase_ms = sum(s[4] for s in steps)
            dur = _format_duration(phase_ms)
            dur_suffix = f" · {dur}" if dur else ""
            bar_pct = min(100, max(8, int(phase_ms / total_ms * 100))) if total_ms > 0 else 100
            pipeline_lines.append(
                f"**Phase {idx} — {phase['title']}**{dur_suffix}  \n"
                f"<span style='color:#64748b;font-size:0.9em'>{phase['blurb']}</span>  \n"
                f"<div style='background:#e2e8f0;border-radius:4px;height:6px;margin:6px 0 10px 0'>"
                f"<div style='background:#0ea5e9;border-radius:4px;height:6px;width:{bar_pct}%'></div></div>"
            )
            for sidx, (step_num, kind, name, detail, ms) in enumerate(steps, start=1):
                kind_label = _KIND_LABELS.get(kind, kind.title() if kind else "Step")
                explain = _explain_step(name, kind, detail)
                ms_label = _format_duration(ms)
                timing = f" · {ms_label}" if ms_label else ""
                label = step_num or sidx
                pipeline_lines.append(
                    f"&nbsp;&nbsp;↳ **{label}. {name}** ({kind_label}){timing} — {explain}"
                )

        total_label = _format_duration(total_ms)
        summary = f"**Total:** {total_label} · {len(items)} step(s)" if total_label else f"**Total:** {len(items)} step(s)"
        st.markdown(
            summary + "\n\n---\n\n" + "\n\n".join(pipeline_lines),
            unsafe_allow_html=True,
        )

        with st.expander("View raw trace"):
            rows = []
            for t in items:
                s, k, n, d, m = _normalize_step(t)
                rows.append(
                    {
                        "step": s,
                        "kind": k,
                        "name": n,
                        "duration_ms": m,
                        "detail": d,
                    }
                )
            st.code(json.dumps(rows, indent=2), language="json")
