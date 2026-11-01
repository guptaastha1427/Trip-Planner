"""
Optional CrewAI multi-agent trip generation (generate mode only).

What: POI Researcher → Itinerary Planner → Grounding Critic pipeline.
Why: Alternative orchestration when ORCHESTRATION_MODE=crew.
How: Deterministic role steps with CrewAI Agent/Task/Crew kickoff when available;
     falls back to the same steps if kickoff does not produce an itinerary.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from pydantic import ValidationError

from google import genai
from google.genai import types

from config import DEFAULT_MODEL, FAST_POI_LIMIT
from services.trip.planning_progress import GENERATE_STEP_TOTAL, emit as plan_step
from services.trip.agent import (
    AgentResult,
    AgentTraceStep,
    _compact_poi_catalog,
    _postprocess_success,
    generate_content_with_fallback,
)
from services.trip.poi_search import search_pois
from services.trip.trace_timing import notify_trace, trace_span
from services.core.validation import (
    enrich_itinerary_from_pois,
    extract_json,
    validate_itinerary_poi_ids,
    validate_itinerary_structure,
    validate_itinerary_unique_pois,
)

# User-visible agent roles (CrewAI multi-agent generate)
CREWAI_AGENT_NAMES: tuple[str, ...] = (
    "POI Researcher",
    "Itinerary Planner",
    "Grounding Critic",
)
CREW_AGENT_ROLES: List[tuple[str, str, str]] = [
    ("poi_researcher", "POI Researcher", "Fetch real places from OpenStreetMap"),
    ("itinerary_planner", "Itinerary Planner", "Draft day-by-day JSON with Gemini"),
    ("grounding_critic", "Grounding Critic", "Validate poi_ids and enrich stops"),
    ("travel_hints", "Travel hints", "Airports, hotels, and practical tips"),
]

_CREW_STEP_TOTAL = GENERATE_STEP_TOTAL


def _crewai_llm_model_string(model: str) -> str:
    """LiteLLM-style model id for CrewAI ``Agent(llm=...)`` (must be str or native BaseLLM)."""
    raw = (model or DEFAULT_MODEL).strip()
    if raw.startswith("models/"):
        raw = raw[len("models/") :]
    if "/" not in raw:
        return f"gemini/{raw}"
    if raw.startswith("google/"):
        return "gemini/" + raw.split("/", 1)[1]
    return raw


def _crew_progress(
    on_progress: Optional[Callable[[str], None]],
    step: int,
    role: str,
    message: str,
) -> None:
    plan_step(on_progress, step, _CREW_STEP_TOTAL, role, message)


def _trace_step(
    trace: List[AgentTraceStep],
    *,
    kind: str,
    name: str,
    duration_ms: float = 0,
    detail: str = "",
    on_trace: Optional[Callable[[List[AgentTraceStep]], None]] = None,
) -> None:
    step_no = (max((s.step for s in trace), default=0) + 1) if trace else 1
    trace.append(
        AgentTraceStep(
            step=step_no,
            kind=kind,
            name=name,
            duration_ms=duration_ms,
            detail=detail,
        )
    )
    notify_trace(trace, on_trace)


def _planner_system_instruction() -> str:
    return (
        "You are a trip planning assistant. Reply with ONLY a JSON object — no markdown, "
        "no code fences. Every activity must use a poi_id from the provided catalog. "
        "Each poi_id may appear at most once in the entire trip — never repeat the same place. "
        "All text must be in English, including each activity name (translate if needed). "
        "Prioritize famous landmarks and notable sights (high _score / museums / historic / "
        "attractions). Mix categories across each day: culture, outdoors, food, shopping — "
        "do not fill the whole trip with only museums or only restaurants."
    )


def _planner_user_text(
    *,
    destination: str,
    trip_days: int,
    pace: str,
    interests: List[str],
    constraints: str,
    catalog: str,
    fix_note: str = "",
) -> str:
    base = (
        f"Plan a {trip_days}-day trip to {destination}.\n"
        f"Pace: {pace}. Interests: {', '.join(interests)}.\n"
        f"Constraints: {constraints or 'none'}.\n\n"
        f"POI catalog (use only these poi_id values):\n{catalog}\n\n"
        "Include iconic must-see places when they appear in the catalog. "
        "Vary stop types morning/afternoon/evening.\n"
        'Schema: {"destination":"...","days":[{"day":1,"morning":[],"afternoon":[],"evening":[]}]}\n'
        'Each activity: {"poi_id":"...","name":"...","why":"one short sentence"}'
    )
    if fix_note:
        base += f"\n\nCorrection required: {fix_note}"
    return base


@dataclass
class _CrewRunContext:
    api_key: str
    model: str
    destination: str
    trip_days: int
    pace: str
    interests: List[str]
    constraints: str
    user_agent: str
    on_progress: Optional[Callable[[str], None]]
    on_trace: Optional[Callable[[List[AgentTraceStep]], None]] = None
    trace: List[AgentTraceStep] = field(default_factory=list)
    tool_state: Dict[str, Any] = field(default_factory=dict)
    catalog: str = ""
    raw_final_text: str = ""
    itinerary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    contents: List[Any] = field(default_factory=list)
    client: Any = None
    config: Any = None

    def poi_researcher(self) -> str:
        if self.tool_state.get("pois"):
            n = len(self.tool_state["pois"])
            _crew_progress(
                self.on_progress,
                1,
                "POI Researcher",
                f"using existing catalog ({n} places)",
            )
            return f"Already collected {n} POIs"
        _crew_progress(
            self.on_progress,
            1,
            "POI Researcher",
            f"searching OpenStreetMap for {self.destination}…",
        )
        poi_limit = min(FAST_POI_LIMIT, 12 + self.trip_days * 3)
        with trace_span(
            self.trace,
            kind="crew",
            name="poi_researcher",
            start_detail=f"OpenStreetMap · {self.destination}…",
            on_trace=self.on_trace,
        ) as set_detail:
            poi_result = search_pois(
                city=self.destination,
                interests=self.interests,
                user_agent=self.user_agent,
                limit=poi_limit,
                fast=True,
            )
            poi_count = len(poi_result.get("pois", {}))
            set_detail(
                str(
                    poi_result.get("error")
                    or f"{poi_count} POIs · limit {poi_limit} · interests: {', '.join(self.interests)}"
                )
            )
        if not poi_result.get("ok"):
            self.error = poi_result.get("error", "POI search failed.")
            return self.error
        self.tool_state = {
            "pois": poi_result["pois"],
            "chunks": [],
            "city_meta": poi_result.get("city_meta"),
        }
        self.catalog = _compact_poi_catalog(poi_result["pois"], poi_limit)
        return f"Collected {len(self.tool_state['pois'])} POIs"

    def itinerary_planner(self, fix_note: str = "") -> str:
        if self.error and not self.tool_state.get("pois"):
            return self.error or "POI step failed"
        revision = " (revision after critic)" if fix_note else ""
        _crew_progress(
            self.on_progress,
            2,
            "Itinerary Planner",
            f"drafting JSON with Gemini{revision}…",
        )
        if not self.client:
            self.client = genai.Client(api_key=self.api_key)
            self.config = types.GenerateContentConfig(
                system_instruction=_planner_system_instruction(),
                temperature=0.2,
            )
        user_text = _planner_user_text(
            destination=self.destination,
            trip_days=self.trip_days,
            pace=self.pace,
            interests=self.interests,
            constraints=self.constraints,
            catalog=self.catalog,
            fix_note=fix_note,
        )
        if fix_note or not self.contents:
            self.contents = [
                types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
            ]
        with trace_span(
            self.trace,
            kind="crew",
            name="itinerary_planner",
            start_detail=f"Gemini drafting JSON · {self.model}…",
            on_trace=self.on_trace,
        ) as set_detail:
            try:
                _, response = generate_content_with_fallback(
                    self.client,
                    self.model,
                    contents=self.contents,
                    config=self.config,
                    on_progress=self.on_progress,
                )
            except Exception as exc:  # noqa: BLE001
                self.error = f"Gemini API error: {exc}"
                set_detail(f"failed · {exc}")
                return self.error
            if not response.candidates:
                self.error = "Gemini returned no candidates."
                set_detail("failed · no candidates")
                return self.error
            self.raw_final_text = (response.text or "").strip()
            attempt = sum(1 for s in self.trace if s.name == "itinerary_planner")
            set_detail(f"Gemini itinerary JSON · attempt {attempt} · model {self.model}")
        return self.raw_final_text[:200]

    def grounding_critic(self) -> str:
        _crew_progress(
            self.on_progress,
            3,
            "Grounding Critic",
            "checking JSON, poi_ids, duplicates, enrichment…",
        )
        detail = "passed"
        with trace_span(
            self.trace,
            kind="crew",
            name="grounding_critic",
            start_detail="validating JSON and poi_ids…",
            on_trace=self.on_trace,
        ) as set_detail:
            try:
                itin = extract_json(self.raw_final_text)
                validate_itinerary_structure(itin, expected_days=self.trip_days)
                validate_itinerary_poi_ids(itin, self.tool_state["pois"])
                validate_itinerary_unique_pois(itin)
                itin = enrich_itinerary_from_pois(itin, self.tool_state["pois"])
                self.itinerary = itin
                stops = sum(
                    len(day.get(blk, []))
                    for day in itin.get("days", [])
                    for blk in ("morning", "afternoon", "evening")
                )
                detail = f"passed · {stops} stops"
            except Exception as exc:  # noqa: BLE001
                detail = str(exc)[:120]
                self.itinerary = None
            set_detail(detail)
        if self.itinerary:
            _crew_progress(
                self.on_progress,
                3,
                "Grounding Critic",
                detail,
            )
            return "VALID"
        _crew_progress(
            self.on_progress,
            3,
            "Grounding Critic",
            f"needs fix: {detail[:80]}",
        )
        return detail

    def run_deterministic_pipeline(self) -> None:
        if not self.tool_state.get("pois"):
            self.poi_researcher()
        if self.error and not self.tool_state.get("pois"):
            return
        fix_note = ""
        for attempt in range(2):
            if not self.raw_final_text or fix_note:
                self.itinerary_planner(fix_note=fix_note)
            if self.error and not self.raw_final_text:
                return
            verdict = self.grounding_critic()
            if self.itinerary:
                _postprocess_success(
                    self.trace, self.tool_state, self.destination, self.user_agent
                )
                return
            if attempt == 0 and verdict != "VALID":
                fix_note = f"Invalid JSON or poi_id. Error: {verdict}. Reply with ONLY corrected JSON."
                self.contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=fix_note)],
                    )
                )
                continue
            self.error = verdict or "Could not validate itinerary."
            return
        self.error = self.error or "Crew itinerary generation failed."


def _try_crewai_kickoff(ctx: _CrewRunContext) -> bool:
    """Run CrewAI sequential crew; tools delegate to ctx role methods."""
    from config import configure_crewai_storage

    configure_crewai_storage()
    if ctx.api_key:
        os.environ["GEMINI_API_KEY"] = ctx.api_key
    import sys

    try:
        from crewai import Agent, Crew, Process, Task
        from crewai.tools import tool
    except ImportError as exc:
        py = f"{sys.version_info.major}.{sys.version_info.minor}"
        hint = (
            f"Run `{sys.executable} -m pip install -r requirements.txt` "
            f"in the same Python you use for Streamlit (now {py}). "
        )
        if sys.version_info >= (3, 14):
            hint += "CrewAI supports Python 3.10–3.13 — use `trip-planner-env` or python3.13."
        _trace_step(
            ctx.trace,
            kind="crew",
            name="crew_kickoff",
            detail=f"CrewAI unavailable ({exc}). {hint} Using direct agent steps.",
            on_trace=ctx.on_trace,
        )
        return False

    with trace_span(
        ctx.trace,
        kind="crew",
        name="crew_kickoff",
        start_detail="CrewAI sequential kickoff (POI Researcher → Planner → Critic)…",
        on_trace=ctx.on_trace,
    ) as set_detail:
        _crew_progress(
            ctx.on_progress,
            0,
            "Crew orchestrator",
            "starting CrewAI sequential agents…",
        )

        @tool("poi_research_for_trip")
        def poi_research_for_trip() -> str:
            """Fetch OpenStreetMap POIs for the trip destination. Call this first."""
            return ctx.poi_researcher()

        @tool("plan_itinerary_json")
        def plan_itinerary_json() -> str:
            """Draft a JSON itinerary from the POI catalog using Gemini."""
            return ctx.itinerary_planner()

        @tool("validate_itinerary_grounding")
        def validate_itinerary_grounding() -> str:
            """Validate JSON structure, poi_ids, uniqueness, and enrich from catalog."""
            return ctx.grounding_critic()

        llm_model = _crewai_llm_model_string(ctx.model or DEFAULT_MODEL)

        try:
            researcher = Agent(
                role="POI Researcher",
                goal="Collect real OpenStreetMap POIs for the trip",
                backstory="You only use the POI research tool; never invent places.",
                tools=[poi_research_for_trip],
                llm=llm_model,
                verbose=False,
                allow_delegation=False,
            )
            planner = Agent(
                role="Itinerary Planner",
                goal="Produce grounded JSON day plans from the POI catalog",
                backstory="You use plan_itinerary_json after POIs exist.",
                tools=[plan_itinerary_json],
                llm=llm_model,
                verbose=False,
                allow_delegation=False,
            )
            critic = Agent(
                role="Grounding Critic",
                goal="Validate itinerary JSON against the POI catalog",
                backstory="You use validate_itinerary_grounding after a draft exists.",
                tools=[validate_itinerary_grounding],
                llm=llm_model,
                verbose=False,
                allow_delegation=False,
            )

            task_poi = Task(
                description=(
                    f"For destination {ctx.destination}, call poi_research_for_trip exactly once."
                ),
                expected_output="POI count summary",
                agent=researcher,
            )
            task_plan = Task(
                description="Call plan_itinerary_json to create the trip JSON.",
                expected_output="Itinerary JSON draft",
                agent=planner,
            )
            task_crit = Task(
                description="Call validate_itinerary_grounding to verify the draft.",
                expected_output="VALID or error detail",
                agent=critic,
            )

            crew = Crew(
                agents=[researcher, planner, critic],
                tasks=[task_poi, task_plan, task_crit],
                process=Process.sequential,
                verbose=False,
            )
            crew.kickoff(
                inputs={
                    "destination": ctx.destination,
                    "trip_days": ctx.trip_days,
                }
            )
            set_detail("Kickoff finished")
        except ValidationError as exc:
            set_detail(
                "CrewAI Agent validation failed (use string llm, not LangChain). "
                f"Using direct agent steps. ({exc})"[:240]
            )
            return False
        except Exception as exc:  # noqa: BLE001
            ctx.error = ctx.error or f"Crew kickoff: {exc}"
            set_detail(f"Kickoff failed: {exc}"[:200])
            _crew_progress(
                ctx.on_progress,
                0,
                "Crew orchestrator",
                "kickoff failed — continuing with direct agent steps…",
            )
            return False
    _trace_step(
        ctx.trace,
        kind="crew",
        name="crew_kickoff_complete",
        detail="Kickoff finished",
        on_trace=ctx.on_trace,
    )
    return True


def run_crew_trip(
    *,
    api_key: str,
    model: str,
    destination: str,
    trip_days: int,
    pace: str,
    interests: List[str],
    constraints: str,
    user_agent: str,
    on_progress: Optional[Callable[[str], None]] = None,
    on_trace: Optional[Callable[[List[AgentTraceStep]], None]] = None,
    **_: Any,
) -> AgentResult:
    """
    Multi-agent generate path. Extra kwargs (e.g. from run_agent) are ignored for v1.
    """
    ctx = _CrewRunContext(
        api_key=api_key,
        model=model or DEFAULT_MODEL,
        destination=destination,
        trip_days=trip_days,
        pace=pace,
        interests=interests,
        constraints=constraints or "",
        user_agent=user_agent,
        on_progress=on_progress,
        on_trace=on_trace,
    )

    _trace_step(
        ctx.trace,
        kind="crew",
        name="crew_start",
        detail=(
            f"Multi-agent generate · {destination} · {trip_days} day(s) · "
            f"pace {pace}"
        ),
        on_trace=on_trace,
    )
    _crew_progress(
        on_progress,
        0,
        "Crew orchestrator",
        f"pipeline ready for {destination}",
    )

    try:
        _try_crewai_kickoff(ctx)
    except ValidationError as exc:
        _trace_step(
            ctx.trace,
            kind="crew",
            name="crew_kickoff",
            detail=f"CrewAI validation error — direct steps ({exc})"[:200],
            on_trace=on_trace,
        )
    if not ctx.itinerary:
        _trace_step(
            ctx.trace,
            kind="crew",
            name="crew_pipeline",
            detail="Running direct POI → Planner → Critic steps",
            on_trace=on_trace,
        )
        ctx.run_deterministic_pipeline()

    if ctx.itinerary and not any(
        s.name == "travel_hints" for s in ctx.trace if s.kind == "postprocess"
    ):
        _crew_progress(
            on_progress,
            4,
            "Travel hints",
            "loading airports, hotels, and tips…",
        )
        _postprocess_success(ctx.trace, ctx.tool_state, ctx.destination, ctx.user_agent)

    if ctx.itinerary:
        return AgentResult(
            ok=True,
            itinerary=ctx.itinerary,
            tool_state=ctx.tool_state,
            trace=ctx.trace,
            raw_final_text=ctx.raw_final_text,
        )
    return AgentResult(
        ok=False,
        itinerary=None,
        tool_state=ctx.tool_state or {"pois": {}, "chunks": [], "city_meta": None},
        trace=ctx.trace,
        raw_final_text=ctx.raw_final_text,
        error=ctx.error or "Crew trip generation failed.",
    )
