"""User-facing display of agent execution trace steps."""

import html
import json
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from services.trip.agent_trace import AgentTraceStep
from services.ui.ui_components import section_heading
from services.trip.planning_progress import GEMINI_PLANNING_STAGES, stage_status_from_trace
from services.trip.trace_timing import effective_duration_ms

# Internal step name -> pipeline phase id
_NAME_TO_PHASE: Dict[str, str] = {
    "agent_start": "start",
    "fast_fallback": "start",
    "crew_start": "crew",
    "crew_kickoff": "crew",
    "crew_kickoff_complete": "crew",
    "crew_pipeline": "crew",
    "poi_researcher": "crew_search",
    "itinerary_planner": "crew_ai",
    "grounding_critic": "crew_validate",
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
        "id": "crew",
        "title": "Crew orchestration",
        "blurb": "Multi-agent pipeline start and CrewAI kickoff.",
    },
    {
        "id": "crew_search",
        "title": "POI Researcher (OpenStreetMap)",
        "blurb": "Agent 1 — collect real places for the catalog.",
    },
    {
        "id": "crew_ai",
        "title": "Itinerary Planner (Gemini)",
        "blurb": "Agent 2 — draft grounded day-by-day JSON.",
    },
    {
        "id": "crew_validate",
        "title": "Grounding Critic",
        "blurb": "Agent 3 — validate poi_ids and enrich stops.",
    },
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
    "crew_start": "Multi-agent crew pipeline started for this trip.",
    "crew_kickoff": "CrewAI sequential orchestration invoked.",
    "crew_kickoff_complete": "CrewAI kickoff completed.",
    "crew_pipeline": "Direct agent steps (POI → Planner → Critic).",
    "poi_researcher": "POI Researcher fetched OpenStreetMap catalog.",
    "itinerary_planner": "Itinerary Planner drafted JSON with Gemini.",
    "grounding_critic": "Grounding Critic validated and enriched stops.",
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
    "crew": "Crew agent",
}

_ORCHESTRATION_TRACE_NAMES = frozenset(
    {
        "agent_start",
        "fast_fallback",
        "crew_start",
        "crew_kickoff",
        "crew_kickoff_complete",
        "crew_pipeline",
        "poi_search_start",
        "complete",
    }
)

_ORCHESTRATION_DISPLAY_TITLES = {
    "agent_start": "Run started",
    "fast_fallback": "Fallback to tool agent",
    "crew_start": "Crew pipeline started",
    "crew_kickoff": "CrewAI kickoff",
    "crew_kickoff_complete": "CrewAI kickoff finished",
    "crew_pipeline": "Direct crew steps",
    "poi_search_start": "POI search phase",
    "complete": "Run finished",
}

_CREW_ROLE_ORDER = (
    "poi_researcher",
    "itinerary_planner",
    "grounding_critic",
    "travel_hints",
    "complete",
)

# Internal trace step name -> user-visible crew agent
_CREW_AGENT_FOR_STEP: Dict[str, str] = {
    "crew_start": "Crew orchestrator",
    "crew_kickoff": "Crew orchestrator",
    "crew_kickoff_complete": "Crew orchestrator",
    "crew_pipeline": "Crew orchestrator",
    "poi_researcher": "POI Researcher",
    "itinerary_planner": "Itinerary Planner",
    "grounding_critic": "Grounding Critic",
    "travel_hints": "Travel hints",
}


def _step_agent_label(name: str) -> str:
    if name in _CREW_AGENT_FOR_STEP:
        return _CREW_AGENT_FOR_STEP[name]
    return name.replace("_", " ").title()


def _crew_role_duration_ms(trace: List[Any], role_name: str) -> float:
    """Sum recorded durations for all trace steps with this role name."""
    total = 0.0
    for t in trace:
        _, _, name, _, _ = _normalize_step(t)
        if name == role_name:
            total += _step_ms(t)
    return total


def _crew_orchestrator_duration_ms(trace: List[Any]) -> float:
    total = 0.0
    for t in trace:
        _, _, name, _, _ = _normalize_step(t)
        if name in (
            "crew_start",
            "crew_kickoff",
            "crew_kickoff_complete",
            "crew_pipeline",
        ):
            total += _step_ms(t)
    return total


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


def _as_trace_step(item: Any) -> AgentTraceStep:
    if isinstance(item, AgentTraceStep):
        return item
    if isinstance(item, dict):
        return AgentTraceStep(
            step=int(item.get("step") or 0),
            kind=str(item.get("kind") or ""),
            name=str(item.get("name") or ""),
            duration_ms=float(item.get("duration_ms") or 0),
            detail=str(item.get("detail") or ""),
            started_at=float(item.get("started_at") or 0),
        )
    return AgentTraceStep(
        step=int(item.step),
        kind=str(item.kind),
        name=str(item.name),
        duration_ms=float(item.duration_ms),
        detail=str(item.detail),
        started_at=float(getattr(item, "started_at", 0) or 0),
    )


def _step_ms(item: Any, *, now: Optional[float] = None) -> float:
    return effective_duration_ms(_as_trace_step(item), now=now or time.time())


def _trace_has_crew_steps(trace: Optional[List[Any]]) -> bool:
    for t in trace or []:
        _, kind, name, _, _ = _normalize_step(t)
        if kind == "crew" or name in _CREW_ROLE_ORDER:
            return True
    return False


def _crew_role_failed(trace: List[Any], role_name: str) -> bool:
    rows = [_normalize_step(t) for t in trace if _normalize_step(t)[2] == role_name]
    if not rows:
        return False
    _, _, _, detail, _ = rows[-1]
    low = detail.lower()
    return "error" in low or "fail" in low or "502" in detail


def _crew_step_status(trace: List[Any], role_name: str) -> Tuple[str, str, str]:
    """Return (status emoji label, detail, duration) for a crew role."""
    rows = [t for t in trace if _normalize_step(t)[2] == role_name]
    if not rows:
        if role_name != "poi_researcher" and _crew_role_failed(trace, "poi_researcher"):
            return (
                "⏭ Skipped",
                "POI Researcher failed — later agents did not run.",
                "",
            )
        return ("⏸ Not run", "—", "")
    last = rows[-1]
    _, kind, name, detail, _ = _normalize_step(last)
    dur = _format_duration(_step_ms(last))
    if role_name == "grounding_critic":
        if detail.lower().startswith("passed") or detail == "passed":
            return ("✅ Passed", detail, dur)
        if detail and detail != "passed":
            return ("⚠ Needs revision", detail, dur)
    if role_name == "itinerary_planner" and len(rows) > 1:
        return (f"✅ Done ({len(rows)} attempts)", detail, dur)
    if kind == "postprocess" or name in ("travel_hints", "complete"):
        return ("✅ Done", detail, dur)
    if "error" in detail.lower() or "fail" in detail.lower():
        return ("❌ Failed", detail, dur)
    return ("✅ Done", detail, dur)


def _render_crew_agent_timing_table(items: List[Any]) -> None:
    """Named crew agents with per-task elapsed time from the trace."""
    from services.trip.crew_trip import CREW_AGENT_ROLES

    st.markdown("**Crew agents & time per task**")
    h = st.columns([0.28, 0.14, 0.58])
    h[0].markdown("**Agent**")
    h[1].markdown("**Time**")
    h[2].markdown("**Task**")

    orch_ms = _crew_orchestrator_duration_ms(items)
    orch_dur = _format_duration(orch_ms) if orch_ms > 0 else "—"
    r0 = st.columns([0.28, 0.14, 0.58])
    r0[0].markdown("**Crew orchestrator**")
    r0[1].markdown(orch_dur if orch_dur else "—")
    r0[2].markdown(
        "Pipeline start, CrewAI kickoff (if available), or direct step handoff"
    )

    for role_id, title, blurb in CREW_AGENT_ROLES:
        ms = _crew_role_duration_ms(items, role_id)
        dur = _format_duration(ms) if ms > 0 else "—"
        c0, c1, c2 = st.columns([0.28, 0.14, 0.58])
        c0.markdown(f"**{title}**")
        c1.markdown(dur)
        c2.markdown(blurb)

def render_planning_summary(
    trace: Optional[List[Any]],
    *,
    orchestration: Optional[str] = None,
    planning_context: Optional[Dict[str, Any]] = None,
) -> None:
    """Checklist of planning steps for crew or default Gemini agent traces."""
    items = list(trace or [])
    if not items:
        return

    is_crew = orchestration == "crew" or _trace_has_crew_steps(items)
    if is_crew:
        st.markdown("**Planning steps (CrewAI multi-agent)**")
        from services.trip.crew_trip import CREWAI_AGENT_NAMES, CREW_AGENT_ROLES

        agents_line = " · ".join(f"**{n}**" for n in CREWAI_AGENT_NAMES)
        st.caption(
            f"CrewAI agents: {agents_line} — then **Travel hints**. "
            "Same roles run via Crew kickoff or direct steps if kickoff is unavailable."
        )
        _render_crew_agent_timing_table(items)

        stages = [(role_id, title, blurb) for role_id, title, blurb in CREW_AGENT_ROLES]
    else:
        st.markdown("**Planning steps (Trip Planner agent)**")
        st.caption(
            "OpenStreetMap places → Gemini itinerary → validation → travel hints "
            "(Wikivoyage/tools when enabled)."
        )
        stages = [
            (names, title, blurb) for names, title, blurb in GEMINI_PLANNING_STAGES
        ]

    hdr = st.columns([0.32, 0.18, 0.12, 0.38])
    hdr[0].markdown("**Stage**")
    hdr[1].markdown("**Status**")
    hdr[2].markdown("**Time**")
    hdr[3].markdown("**What happened**")

    for stage in stages:
        if is_crew:
            role_id, title, blurb = stage
            status, detail, dur = _crew_step_status(items, role_id)
            if not dur:
                ms = _crew_role_duration_ms(items, role_id)
                dur = _format_duration(ms) if ms > 0 else ""
        else:
            names, title, blurb = stage
            status, detail, dur = stage_status_from_trace(items, names)
            if status == "⏸ Not run" and names == ("retrieve_guides",):
                continue
        time_cell = dur if dur else "—"
        c0, c1, c2, c3 = st.columns([0.32, 0.18, 0.12, 0.38])
        c0.markdown(
            f"**{title}**  \n<span style='color:#64748b;font-size:0.85em'>{blurb}</span>",
            unsafe_allow_html=True,
        )
        c1.markdown(status)
        c2.markdown(f"**{time_cell}**" if time_cell != "—" else time_cell)
        c3.markdown(
            detail
            if detail != "—"
            else (
                "_Waiting for an earlier stage_"
                if status == "⏸ Not run"
                else "_Not used in this run_"
            )
        )

    _render_orchestration_setup_log(
        items,
        orchestration=orchestration,
        planning_context=planning_context,
    )


def _render_orchestration_setup_log(
    items: List[Any],
    *,
    orchestration: Optional[str],
    planning_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Show how the run was configured (mode, trip) plus setup steps from the trace.

    This is the technical counterpart to the high-level planning checklist above.
    """
    ctx = planning_context or {}
    mode_label = str(ctx.get("mode") or "generate").replace("_", " ")
    orch = orchestration or ctx.get("orchestration") or "gemini"
    if orch == "crew":
        path_label = "CrewAI multi-agent (POI Researcher → Planner → Critic)"
    elif mode_label != "generate":
        path_label = f"Gemini agent · {mode_label}"
    else:
        path_label = "Gemini agent · fast generate (OSM + one Gemini call)"

    summary_lines = [
        f"**Orchestration:** `{orch}` — {path_label}",
    ]
    dest = ctx.get("destination")
    if dest:
        summary_lines.append(
            f"**Trip:** {dest} · **{ctx.get('trip_days', '?')}** day(s) · pace **{ctx.get('pace', '—')}**"
        )
    model = ctx.get("model")
    if model:
        summary_lines.append(f"**Model:** `{model}`")
    if ctx.get("fast_mode") is not None and orch != "crew":
        summary_lines.append(
            f"**Fast mode:** {'on' if ctx.get('fast_mode') else 'off'}"
            + (" (Wikivoyage tool off in fast path)" if ctx.get("fast_mode") else "")
        )
    if ctx.get("ok") is False:
        summary_lines.append("**Last run:** failed before a valid itinerary was saved.")

    trace_rows = [
        _normalize_step(t)
        for t in items
        if _normalize_step(t)[2] in _ORCHESTRATION_TRACE_NAMES
    ]

    with st.expander("Orchestration & setup log", expanded=False):
        st.caption(
            "Run configuration and startup events: which path ran (Gemini vs Crew), "
            "trip settings, and any fallback or crew kickoff steps from the agent trace."
        )
        st.markdown("  \n".join(summary_lines))
        if trace_rows:
            st.markdown("**Events from this run**")
            for step_num, kind, name, detail, ms in trace_rows:
                title = _ORCHESTRATION_DISPLAY_TITLES.get(name, name.replace("_", " "))
                agent = _step_agent_label(name)
                if agent != title and agent not in title:
                    title = f"{agent} — {title}"
                explain = _STEP_EXPLANATIONS.get(name, detail)
                dur = _format_duration(ms)
                timing = f" · {dur}" if dur else ""
                body = detail if detail and detail != explain else explain
                if detail and explain and detail not in explain:
                    body = f"{explain} — {detail}"
                st.markdown(f"- **{title}**{timing}: {body}")
        else:
            st.info(
                "No separate setup events were recorded; the planner went straight to "
                "OpenStreetMap and Gemini. After your next **Create my itinerary**, "
                "entries like *Run started* appear here."
            )


def render_crew_planning_summary(trace: Optional[List[Any]]) -> None:
    """Backward-compatible alias."""
    render_planning_summary(trace, orchestration="crew")


def _phase_for_name(name: str, kind: str) -> str:
    if name in _NAME_TO_PHASE:
        return _NAME_TO_PHASE[name]
    if kind == "crew":
        if name in ("poi_researcher",):
            return "crew_search"
        if name in ("itinerary_planner",):
            return "crew_ai"
        if name in ("grounding_critic",):
            return "crew_validate"
        return "crew"
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
        if detail and name in (
            "search_pois",
            "retrieve_guides",
            "poi_search_start",
            "poi_researcher",
            "itinerary_planner",
            "grounding_critic",
        ):
            return f"{base} ({detail})."
        if detail and name in ("surgical_refine", "parse_validate", "parse_retry"):
            return f"{base} {detail}."
        if detail and name == "enrich_itinerary":
            return f"{base} {detail}."
        if detail and name.startswith("crew_"):
            return f"{base} ({detail})."
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


def _sorted_phase_rows(
    entries: List[Tuple[int, Tuple[int, str, str, str, float]]],
) -> List[Tuple[int, str, str, str, float]]:
    """Preserve run order within each phase (matches agent execution sequence)."""
    return [row for _, row in sorted(entries, key=lambda t: t[0])]


def _execution_phases_html(
    visible_phases: List[Dict[str, str]],
    by_phase: Dict[str, List[Tuple[int, Tuple[int, str, str, str, float]]]],
    items: List[Any],
    *,
    now: Optional[float] = None,
) -> str:
    """Card-style HTML blocks so each pipeline phase reads as a distinct panel."""
    now = now or time.time()
    blocks: List[str] = []
    for idx, phase in enumerate(visible_phases, start=1):
        steps = _sorted_phase_rows(by_phase.get(phase["id"], []))
        phase_ms = sum(
            _step_ms(items[trace_idx], now=now)
            for trace_idx, _ in by_phase.get(phase["id"], [])
            if trace_idx < len(items)
        )
        dur = _format_duration(phase_ms)
        time_label = html.escape(dur) if dur else "instant"

        step_rows: List[str] = []
        for sidx, (trace_idx, row) in enumerate(
            sorted(by_phase.get(phase["id"], []), key=lambda t: t[0]), start=1
        ):
            step_num, kind, name, detail, _ = row
            kind_label = _KIND_LABELS.get(kind, kind.title() if kind else "Step")
            agent_label = _step_agent_label(name)
            explain = html.escape(_explain_step(name, kind, detail))
            ms_label = _format_duration(_step_ms(items[trace_idx], now=now))
            running = (
                trace_idx < len(items)
                and _as_trace_step(items[trace_idx]).duration_ms <= 0
                and _as_trace_step(items[trace_idx]).started_at > 0
            )
            if running:
                timing = f" · ⏳ {ms_label} running"
            elif ms_label:
                timing = f" · **{ms_label}**"
            else:
                timing = " · —"
            step_rows.append(
                f'<div class="trace-exec-step">'
                f"↳ <strong>{sidx}. {html.escape(agent_label)}</strong> "
                f'(<span class="trace-exec-step__kind">{html.escape(kind_label)}</span>)'
                f"{timing} — {explain}"
                f"</div>"
            )

        steps_html = (
            f'<div class="trace-exec-phase__steps">{"".join(step_rows)}</div>'
            if step_rows
            else ""
        )
        blocks.append(
            f'<div class="trace-exec-phase">'
            f'<div class="trace-exec-phase__head">'
            f'<span class="trace-exec-phase__num">{idx}</span>'
            f"<div>"
            f'<div class="trace-exec-phase__title">Phase {idx} — '
            f"{html.escape(phase['title'])}</div>"
            f'<div class="trace-exec-phase__blurb">{html.escape(phase["blurb"])}</div>'
            f"</div>"
            f'<span class="trace-exec-phase__time">{time_label}</span>'
            f"</div>"
            f"{steps_html}"
            f"</div>"
        )

    return f'<div class="trace-exec-stack">{"".join(blocks)}</div>'


def render_agent_execution_trace(
    trace: Optional[List[Any]],
    *,
    orchestration: Optional[str] = None,
    agent_mode: Optional[str] = None,
    planning_context: Optional[Dict[str, Any]] = None,
) -> None:
    """Bottom-of-page timeline of agent steps (dict or AgentTraceStep items)."""
    items = list(trace or [])
    with st.container(border=True):
        section_heading("Debug & agent execution", "refine")
        if not items:
            st.caption("Generate an itinerary to see agent steps.")
            return

        if agent_mode and agent_mode != "generate":
            st.caption(f"Last run mode: **{agent_mode.replace('_', ' ')}**")

        normalized = [_normalize_step(t) for t in items]
        now = time.time()
        total_ms = sum(_step_ms(t, now=now) for t in items)

        by_phase: Dict[str, List[Tuple[int, Tuple[int, str, str, str, float]]]] = defaultdict(list)
        for trace_idx, row in enumerate(normalized):
            step_num, kind, name, detail, ms = row
            by_phase[_phase_for_name(name, kind)].append((trace_idx, row))

        visible_phases = [p for p in _PHASES if by_phase.get(p["id"])]
        if not visible_phases:
            visible_phases = [_PHASES[0]]

        total_label = _format_duration(total_ms)
        summary = f"**Total:** {total_label} · {len(items)} step(s)" if total_label else f"**Total:** {len(items)} step(s)"
        st.markdown(summary, unsafe_allow_html=True)
        st.markdown(
            _execution_phases_html(visible_phases, by_phase, items, now=now),
            unsafe_allow_html=True,
        )

        with st.expander("Planning steps summary"):
            render_planning_summary(
                items,
                orchestration=orchestration,
                planning_context=planning_context,
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


def render_live_trace_markdown(trace: Optional[List[Any]]) -> str:
    """Compact live trace while the agent is running (includes in-flight step times)."""
    items = list(trace or [])
    if not items:
        return ""
    now = time.time()
    total = _format_duration(sum(_step_ms(t, now=now) for t in items))
    lines: List[str] = []
    for t in items[-18:]:
        step = _as_trace_step(t)
        ms = _step_ms(t, now=now)
        dur = _format_duration(ms)
        running = step.duration_ms <= 0 and step.started_at > 0
        badge = f"⏳ **{dur}** running" if running else f"**{dur}**" if dur else "**—**"
        agent = _step_agent_label(step.name)
        lines.append(
            f"- {badge} · **{agent}** (`{step.name}`) — "
            f"{html.escape(step.detail[:140])}"
        )
    return (
        f"**Execution trace (live)** · total {total} · {len(items)} step(s)\n\n"
        + "\n".join(lines)
    )
