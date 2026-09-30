"""
Trip planning agent using Google Gemini + function calling.

What: Orchestrates search_pois and retrieve_guides, then produces itinerary JSON.
Why: Gemini supports native tool calls for reliable POI-grounded planning.
How: generate_content loop with function_response parts until final JSON text.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from google import genai
from google.genai import types

from config import (
    DEFAULT_MAX_STEPS,
    FAST_MODE_MAX_STEPS,
    FAST_POI_LIMIT,
    MAX_RETRIES,
    MODEL_FALLBACKS,
)
from services.geocoding import geocode_city
from services.poi_search import search_pois
from services.refine_itinerary import (
    _quoted_phrase,
    ensure_refinement_changed,
    extract_place_phrase,
    is_add_only_request,
    try_surgical_refine,
)
from services.validation import (
    BLOCKS,
    enrich_itinerary_from_pois,
    extract_json,
    validate_itinerary_poi_ids,
    validate_itinerary_structure,
    validate_itinerary_unique_pois,
)
from services.retry_utils import call_with_retries, is_retryable_error
from services.travel_hints import attach_travel_hints
from services.wikivoyage_rag import retrieve_guides


def _gemini_tools() -> List[types.Tool]:
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_pois",
                    description=(
                        "Geocode a city and fetch OpenStreetMap POIs by interests. "
                        "Returns poi_id, name, category, lat, lon, url."
                    ),
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "city": types.Schema(type=types.Type.STRING),
                            "interests": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.STRING),
                            ),
                            "limit": types.Schema(type=types.Type.INTEGER),
                            "query_text": types.Schema(type=types.Type.STRING),
                        },
                        required=["city", "interests", "limit"],
                    ),
                ),
                types.FunctionDeclaration(
                    name="retrieve_guides",
                    description="Retrieve Wikivoyage guide chunks for RAG context.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "destination": types.Schema(type=types.Type.STRING),
                            "query": types.Schema(type=types.Type.STRING),
                        },
                        required=["destination", "query"],
                    ),
                ),
            ]
        )
    ]


@dataclass
class AgentTraceStep:
    step: int
    kind: str
    name: str
    duration_ms: float
    detail: str


@dataclass
class AgentResult:
    ok: bool
    itinerary: Optional[Dict]
    tool_state: Dict
    trace: List[AgentTraceStep] = field(default_factory=list)
    raw_final_text: str = ""
    error: Optional[str] = None


def _merge_pois(tool_state: Dict, new_pois: Dict[str, dict]) -> None:
    tool_state["pois"].update(new_pois)


def _copy_tool_state(initial: Optional[Dict]) -> Dict:
    if not initial:
        return {"pois": {}, "chunks": [], "city_meta": None}
    return {
        "pois": dict(initial.get("pois") or {}),
        "chunks": list(initial.get("chunks") or []),
        "city_meta": initial.get("city_meta"),
        "travel_hints": initial.get("travel_hints"),
        "origin_city": initial.get("origin_city"),
        "_hints_key": initial.get("_hints_key"),
        "_photos_key": initial.get("_photos_key"),
    }


_REFINE_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "go",
        "want",
        "i",
        "we",
        "my",
        "add",
        "visit",
        "include",
        "please",
        "more",
        "less",
        "trip",
        "day",
        "itinerary",
        "make",
        "with",
        "and",
    }
)


def _refine_search_phrase(user_request: str) -> str:
    words = [
        w
        for w in re.split(r"\W+", user_request)
        if len(w) > 2 and w.lower() not in _REFINE_STOPWORDS
    ]
    return " ".join(words) if words else user_request.strip()


def _add_geocoded_place(
    tool_state: Dict,
    phrase: str,
    destination: str,
    user_agent: str,
) -> None:
    if not phrase.strip():
        return
    from services.refine_itinerary import upsert_geocoded_poi

    upsert_geocoded_poi(
        tool_state.setdefault("pois", {}),
        phrase,
        destination,
        user_agent,
    )


def _seed_pois_from_itinerary(tool_state: Dict, itinerary: Optional[dict]) -> None:
    """Keep poi_id validation working when refining from a saved itinerary."""
    if not itinerary:
        return
    pois = tool_state.setdefault("pois", {})
    for day in itinerary.get("days", []):
        for block in BLOCKS:
            for item in day.get(block, []):
                pid = item.get("poi_id")
                if not pid or pid in pois:
                    continue
                if item.get("lat") is None or item.get("lon") is None:
                    continue
                pois[pid] = {
                    "poi_id": pid,
                    "name": item.get("name", "POI"),
                    "category": item.get("category", "poi"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "url": item.get("url", ""),
                }


def _merge_chunks(tool_state: Dict, chunks: List[dict]) -> None:
    seen = {c["chunk_id"] for c in tool_state["chunks"]}
    for ch in chunks:
        if ch["chunk_id"] not in seen:
            tool_state["chunks"].append(ch)
            seen.add(ch["chunk_id"])


def _model_candidates(primary: str) -> List[str]:
    seen: set = set()
    ordered: List[str] = []
    for name in (primary, *MODEL_FALLBACKS):
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _is_model_unavailable_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "404" in msg
        or "not found" in msg
        or ("model" in msg and ("invalid" in msg or "unsupported" in msg))
    )


def generate_content_with_fallback(
    client: genai.Client,
    model: str,
    *,
    contents: List[types.Content],
    config: types.GenerateContentConfig,
    on_progress: Optional[Callable[[str], None]] = None,
) -> tuple[str, Any]:
    """Try primary model, then MODEL_FALLBACKS when the model id is invalid."""
    last_exc: Optional[BaseException] = None
    for candidate in _model_candidates(model):
        try:
            response = client.models.generate_content(
                model=candidate,
                contents=contents,
                config=config,
            )
            return candidate, response
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if _is_model_unavailable_error(exc):
                if on_progress:
                    on_progress(f"Model {candidate} unavailable — trying next…")
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("No Gemini model succeeded")


def _compact_poi_catalog(pois: Dict[str, dict], max_items: int) -> str:
    ranked = sorted(pois.values(), key=lambda p: p.get("_score", 0), reverse=True)
    slim = [
        {
            "poi_id": p["poi_id"],
            "name": p["name"],
            "category": p.get("category", "poi"),
        }
        for p in ranked[:max_items]
    ]
    return json.dumps(slim, ensure_ascii=False)


def _trace_step(
    trace: List[AgentTraceStep],
    *,
    kind: str,
    name: str,
    duration_ms: float = 0,
    detail: str = "",
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


def _postprocess_success(
    trace: List[AgentTraceStep],
    tool_state: Dict,
    destination: str,
    user_agent: str,
) -> None:
    t0 = time.time()
    attach_travel_hints(tool_state, destination, user_agent)
    _trace_step(
        trace,
        kind="postprocess",
        name="travel_hints",
        duration_ms=(time.time() - t0) * 1000,
        detail="Airports, hotels, and tips",
    )
    _trace_step(trace, kind="agent", name="complete", detail="Itinerary ready")


def _finalize_itinerary(
    final_text: str,
    tool_state: Dict,
    trip_days: int,
    mode: str,
    parse_attempts: int,
    on_progress: Optional[Callable[[str], None]],
    trace: Optional[List[AgentTraceStep]] = None,
) -> tuple[Optional[dict], Optional[str]]:
    parse_error: Optional[str] = None
    itin: Optional[dict] = None
    for parse_attempt in range(parse_attempts):
        t0 = time.time()
        try:
            itin = extract_json(final_text)
            validate_itinerary_structure(
                itin, expected_days=trip_days if mode == "generate" else None
            )
            validate_itinerary_poi_ids(itin, tool_state["pois"])
            validate_itinerary_unique_pois(itin)
            if trace is not None:
                _trace_step(
                    trace,
                    kind="validate",
                    name="parse_validate",
                    duration_ms=(time.time() - t0) * 1000,
                    detail="JSON structure and poi_id checks passed",
                )
            t1 = time.time()
            itin = enrich_itinerary_from_pois(itin, tool_state["pois"])
            if trace is not None:
                stop_count = sum(
                    len(day.get(block, []))
                    for day in itin.get("days", [])
                    for block in BLOCKS
                )
                _trace_step(
                    trace,
                    kind="postprocess",
                    name="enrich_itinerary",
                    duration_ms=(time.time() - t1) * 1000,
                    detail=f"{stop_count} stops grounded to map data",
                )
            return itin, None
        except ValueError as exc:
            parse_error = str(exc)
            if trace is not None and parse_attempt == parse_attempts - 1:
                _trace_step(
                    trace,
                    kind="validate",
                    name="parse_validate",
                    duration_ms=(time.time() - t0) * 1000,
                    detail=parse_error[:120],
                )
    return None, parse_error


def _run_fast_generate(
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
) -> AgentResult:
    """One OSM fetch + one Gemini call (no tool loop)."""
    trace: List[AgentTraceStep] = []
    _trace_step(trace, kind="agent", name="agent_start", detail="fast generate")
    poi_limit = min(FAST_POI_LIMIT, 12 + trip_days * 3)

    if on_progress:
        on_progress("Fetching POIs from OpenStreetMap…")
    _trace_step(
        trace,
        kind="phase",
        name="poi_search_start",
        detail=f"{destination} · limit {poi_limit}",
    )
    t0 = time.time()
    poi_result = search_pois(
        city=destination,
        interests=interests,
        user_agent=user_agent,
        limit=poi_limit,
        fast=True,
    )
    trace.append(
        AgentTraceStep(
            step=1,
            kind="tool",
            name="search_pois",
            duration_ms=(time.time() - t0) * 1000,
            detail=str(poi_result.get("error") or f"{len(poi_result.get('pois', {}))} POIs"),
        )
    )
    if not poi_result.get("ok"):
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state={"pois": {}, "chunks": [], "city_meta": None},
            trace=trace,
            error=poi_result.get("error", "POI search failed."),
        )

    tool_state: Dict = {
        "pois": poi_result["pois"],
        "chunks": [],
        "city_meta": poi_result.get("city_meta"),
    }
    catalog = _compact_poi_catalog(poi_result["pois"], poi_limit)

    system_instruction = (
        "You are a trip planning assistant. Reply with ONLY a JSON object — no markdown, "
        "no code fences. Every activity must use a poi_id from the provided catalog. "
        "Each poi_id may appear at most once in the entire trip — never repeat the same place. "
        "All text must be in English, including each activity name (translate if needed). "
        "Prioritize famous landmarks and notable sights (high _score / museums / historic / "
        "attractions). Mix categories across each day: culture, outdoors, food, shopping — "
        "do not fill the whole trip with only museums or only restaurants."
    )
    user_text = (
        f"Plan a {trip_days}-day trip to {destination}.\n"
        f"Pace: {pace}. Interests: {', '.join(interests)}.\n"
        f"Constraints: {constraints or 'none'}.\n\n"
        f"POI catalog (use only these poi_id values):\n{catalog}\n\n"
        "Include iconic must-see places when they appear in the catalog. "
        "Vary stop types morning/afternoon/evening.\n"
        'Schema: {"destination":"...","days":[{"day":1,"morning":[],"afternoon":[],"evening":[]}]}\n'
        'Each activity: {"poi_id":"...","name":"...","why":"one short sentence"}'
    )
    contents = [
        types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
    ]
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2,
    )

    final_text = ""
    for attempt in range(2):
        if on_progress:
            on_progress(
                "Building itinerary with Gemini…"
                if attempt == 0
                else "Fixing itinerary JSON…"
            )
        t1 = time.time()
        try:
            _, response = generate_content_with_fallback(
                client,
                model,
                contents=contents,
                config=config,
                on_progress=on_progress,
            )
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                ok=False,
                itinerary=None,
                tool_state=tool_state,
                trace=trace,
                error=f"Gemini API error: {exc}",
            )
        if not response.candidates:
            return AgentResult(
                ok=False,
                itinerary=None,
                tool_state=tool_state,
                trace=trace,
                error="Gemini returned no candidates.",
            )
        final_text = (response.text or "").strip()
        trace.append(
            AgentTraceStep(
                step=attempt + 1,
                kind="model",
                name="fast_generate",
                duration_ms=(time.time() - t1) * 1000,
                detail="Single-shot itinerary",
            )
        )
        itin, parse_error = _finalize_itinerary(
            final_text,
            tool_state,
            trip_days,
            "generate",
            1,
            on_progress,
            trace=trace,
        )
        if itin:
            _postprocess_success(trace, tool_state, destination, user_agent)
            return AgentResult(
                ok=True,
                itinerary=itin,
                tool_state=tool_state,
                trace=trace,
                raw_final_text=final_text,
            )
        if attempt == 0 and parse_error:
            contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=(
                                "Invalid JSON or poi_id. Error: "
                                f"{parse_error}. Reply with ONLY corrected JSON."
                            )
                        )
                    ],
                )
            )
            continue
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            raw_final_text=final_text,
            error=parse_error or "Could not parse itinerary JSON.",
        )

    return AgentResult(
        ok=False,
        itinerary=None,
        tool_state=tool_state,
        trace=trace,
        raw_final_text=final_text,
        error="Fast itinerary generation failed.",
    )


def _run_fast_refine(
    *,
    api_key: str,
    model: str,
    destination: str,
    trip_days: int,
    pace: str,
    interests: List[str],
    constraints: str,
    user_agent: str,
    mode: str,
    existing_itinerary: dict,
    target_day: Optional[int],
    user_request: str,
    tool_state: Dict,
    on_progress: Optional[Callable[[str], None]] = None,
) -> AgentResult:
    """OSM lookup for the request + one Gemini call (refine / single-day)."""
    trace: List[AgentTraceStep] = []
    _trace_step(trace, kind="agent", name="agent_start", detail=f"fast {mode}")
    _seed_pois_from_itinerary(tool_state, existing_itinerary)
    phrase = _refine_search_phrase(user_request)
    extra_interests = list(dict.fromkeys(interests + [w for w in phrase.split() if len(w) > 3]))

    if is_add_only_request(user_request):
        if on_progress:
            on_progress("Looking up that place and adding it to your trip…")
        quick = try_surgical_refine(
            existing_itinerary,
            tool_state["pois"],
            user_request,
            phrase,
            target_day=target_day,
            destination=destination,
            user_agent=user_agent,
        )
        if quick:
            trace.append(
                AgentTraceStep(
                    step=1,
                    kind="tool",
                    name="surgical_refine",
                    duration_ms=0,
                    detail=user_request[:80],
                )
            )
            _postprocess_success(trace, tool_state, destination, user_agent)
            return AgentResult(
                ok=True,
                itinerary=quick,
                tool_state=tool_state,
                trace=trace,
                raw_final_text="",
            )

    if on_progress:
        on_progress("Searching OpenStreetMap for places in your request…")
    _trace_step(trace, kind="phase", name="poi_search_start", detail=destination)
    t0 = time.time()
    broad = search_pois(
        city=destination,
        interests=extra_interests,
        user_agent=user_agent,
        limit=min(FAST_POI_LIMIT, 45),
        query_text=None,
        fast=True,
    )
    if broad.get("ok") and broad.get("pois"):
        _merge_pois(tool_state, broad["pois"])
        if broad.get("city_meta"):
            tool_state["city_meta"] = broad["city_meta"]

    poi_result = search_pois(
        city=destination,
        interests=extra_interests,
        user_agent=user_agent,
        limit=min(FAST_POI_LIMIT, 45),
        query_text=phrase,
        fast=True,
    )
    if poi_result.get("ok") and poi_result.get("pois"):
        _merge_pois(tool_state, poi_result["pois"])
        if poi_result.get("city_meta"):
            tool_state["city_meta"] = poi_result["city_meta"]

    trace.append(
        AgentTraceStep(
            step=1,
            kind="tool",
            name="search_pois",
            duration_ms=(time.time() - t0) * 1000,
            detail=f"{len(tool_state.get('pois', {}))} POIs in catalog",
        )
    )

    _add_geocoded_place(tool_state, phrase, destination, user_agent)
    quoted = _quoted_phrase(user_request)
    if quoted:
        _add_geocoded_place(tool_state, quoted, destination, user_agent)
        _add_geocoded_place(tool_state, quoted, "", user_agent)
    place_name = extract_place_phrase(user_request)
    if place_name and place_name != phrase:
        _add_geocoded_place(tool_state, place_name, destination, user_agent)
        _add_geocoded_place(tool_state, place_name, "", user_agent)

    if not tool_state.get("pois"):
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            error="No POIs available to refine this trip. Try generating again first.",
        )

    if on_progress:
        on_progress("Applying your change (keeping the rest of the trip the same)…")
    surgical = try_surgical_refine(
        existing_itinerary,
        tool_state["pois"],
        user_request,
        phrase,
        target_day=target_day,
        destination=destination,
        user_agent=user_agent,
    )
    if surgical:
        trace.append(
            AgentTraceStep(
                step=2,
                kind="tool",
                name="surgical_refine",
                duration_ms=0,
                detail=user_request[:80],
            )
        )
        _postprocess_success(trace, tool_state, destination, user_agent)
        return AgentResult(
            ok=True,
            itinerary=surgical,
            tool_state=tool_state,
            trace=trace,
            raw_final_text="",
        )

    if is_add_only_request(user_request):
        itin, change_error = ensure_refinement_changed(
            existing_itinerary,
            None,
            tool_state["pois"],
            user_request,
            phrase,
            target_day=target_day,
            destination=destination,
            user_agent=user_agent,
        )
        if itin:
            _trace_step(
                trace,
                kind="postprocess",
                name="enrich_itinerary",
                detail="Add-only refinement applied",
            )
            _postprocess_success(trace, tool_state, destination, user_agent)
            return AgentResult(
                ok=True,
                itinerary=itin,
                tool_state=tool_state,
                trace=trace,
                raw_final_text="",
            )
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            error=change_error or "Could not add that place.",
        )

    catalog = _compact_poi_catalog(tool_state["pois"], min(60, len(tool_state["pois"])))
    if mode == "single_day" and target_day:
        task = (
            f"ONLY change day {target_day}. All other days must stay exactly the same.\n"
            f"Request: {user_request}"
        )
    else:
        task = f"Refine the full itinerary. Request: {user_request}"

    system_instruction = (
        "You are a trip planning assistant. Reply with ONLY a JSON object — no markdown. "
        "Use only poi_id values from the POI catalog. Each poi_id at most once in the trip. "
        "All text in English. "
        "Make the SMALLEST change needed: keep every other day and stop identical unless "
        "the user explicitly asks to replan the whole trip. For 'add X', insert one stop only. "
        "Do not return an identical itinerary."
    )
    user_text = (
        f"Destination: {destination}. Trip: {trip_days} days, pace: {pace}.\n"
        f"Constraints: {constraints or 'none'}.\n"
        f"{task}\n\n"
        f"POI catalog:\n{catalog}\n\n"
        f"Current itinerary:\n{json.dumps(existing_itinerary, ensure_ascii=False)}\n\n"
        "Return the FULL updated itinerary JSON (all days), same schema: "
        '{"destination":"...","days":[{"day":1,"morning":[],"afternoon":[],"evening":[]}]} '
        "Each activity: {\"poi_id\":\"...\",\"name\":\"...\",\"why\":\"...\"}"
    )
    client = genai.Client(api_key=api_key)
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_text)])]

    final_text = ""
    parse_error: Optional[str] = None
    itin: Optional[dict] = None
    for attempt in range(3):
        temp = 0.25 + attempt * 0.15
        config = types.GenerateContentConfig(
            system_instruction=system_instruction, temperature=temp
        )
        if on_progress:
            on_progress(
                "Applying your refinement…"
                if attempt == 0
                else "Fixing refinement JSON…"
            )
        t1 = time.time()
        try:
            _, response = generate_content_with_fallback(
                client,
                model,
                contents=contents,
                config=config,
                on_progress=on_progress,
            )
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                ok=False,
                itinerary=None,
                tool_state=tool_state,
                trace=trace,
                error=f"Gemini API error: {exc}",
            )
        if not response.candidates:
            return AgentResult(
                ok=False,
                itinerary=None,
                tool_state=tool_state,
                trace=trace,
                error="Gemini returned no candidates.",
            )
        final_text = (response.text or "").strip()
        trace.append(
            AgentTraceStep(
                step=attempt + 1,
                kind="model",
                name="fast_refine",
                duration_ms=(time.time() - t1) * 1000,
                detail=task[:80],
            )
        )
        itin, parse_error = _finalize_itinerary(
            final_text,
            tool_state,
            trip_days,
            mode,
            1,
            on_progress,
            trace=trace,
        )
        if itin:
            break
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            f"Invalid JSON or poi_id. Error: {parse_error}. "
                            "Reply with ONLY corrected full itinerary JSON."
                        )
                    )
                ],
            )
        )

    itin, change_error = ensure_refinement_changed(
        existing_itinerary,
        itin,
        tool_state["pois"],
        user_request,
        phrase,
        target_day=target_day,
        destination=destination,
        user_agent=user_agent,
    )
    if change_error or not itin:
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            raw_final_text=final_text,
            error=change_error or parse_error or "Could not apply refinement.",
        )

    _postprocess_success(trace, tool_state, destination, user_agent)
    return AgentResult(
        ok=True,
        itinerary=itin,
        tool_state=tool_state,
        trace=trace,
        raw_final_text=final_text,
    )


def _args_to_dict(raw: Any) -> dict:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if hasattr(raw, "items"):
        return dict(raw)
    return {}


def _run_tool(
    name: str,
    arguments: dict,
    user_agent: str,
    rag_enabled: bool,
    *,
    fast_mode: bool = False,
) -> dict:
    if name == "search_pois":
        q = arguments.get("query_text")
        raw_limit = int(arguments.get("limit", 30))
        limit = min(raw_limit, FAST_POI_LIMIT) if fast_mode else raw_limit
        return search_pois(
            city=arguments["city"],
            interests=arguments["interests"],
            user_agent=user_agent,
            limit=limit,
            query_text=q if q else None,
            fast=fast_mode,
        )
    if name == "retrieve_guides":
        return retrieve_guides(
            destination=arguments["destination"],
            query=arguments["query"],
            user_agent=user_agent,
            enabled=rag_enabled,
        )
    return {"ok": False, "error": f"Unknown tool: {name}"}


def _build_system_instructions(
    trip_days: int,
    pace: str,
    constraints: str,
    fast_mode: bool,
    mode: str,
    existing_itinerary: Optional[dict],
    target_day: Optional[int],
    user_request: Optional[str],
) -> str:
    tool_hint = (
        "Call search_pois ONCE with limit=40."
        if fast_mode
        else "Call search_pois 2-3 times with limit=30 each."
    )
    base = f"""
You are a trip planning agent. Use tools to discover real POIs; never invent poi_id values.

Trip: {trip_days} days, pace: {pace}.
Constraints: {constraints or 'none'}.
Tool strategy: {tool_hint}. Optionally call retrieve_guides.

Final answer MUST be ONLY a JSON object (no markdown):
{{"destination":"...","days":[{{"day":1,"morning":[...],"afternoon":[...],"evening":[...]}}]}}
Use only poi_id values from search_pois. Never use the same poi_id twice in one itinerary.
Write all names and why fields in English only.
Prefer famous landmarks (museums, historic sites, attractions) and mix stop types each day —
avoid repeating only one category (e.g. all restaurants).
"""
    if mode == "refine" and existing_itinerary and user_request:
        return (
            base
            + "\nREFINEMENT TASK: Update the itinerary per the user request below.\n"
            + "- If they name a new place (museum, venue, restaurant), call search_pois with "
            "query_text set to that place or theme before final JSON.\n"
            + "- Swap or add activities using only poi_id values from search_pois results "
            "(including existing catalog).\n"
            + "- Keep the same number of days unless the user explicitly asks to change length.\n"
            + f"\nUser request: {user_request}\n"
            + f"Current itinerary JSON:\n{json.dumps(existing_itinerary)}"
        )
    if mode == "single_day" and existing_itinerary and target_day and user_request:
        return (
            base
            + f"\nONLY modify day {target_day}. Other days unchanged.\n"
            + json.dumps(existing_itinerary)
            + f"\nRequest: {user_request}"
        )
    return base


def run_agent(
    *,
    api_key: str,
    model: str,
    destination: str,
    trip_days: int,
    pace: str,
    interests: List[str],
    constraints: str,
    user_agent: str,
    fast_mode: bool = False,
    max_steps: Optional[int] = None,
    rag_enabled: bool = False,
    mode: str = "generate",
    existing_itinerary: Optional[dict] = None,
    target_day: Optional[int] = None,
    user_request: Optional[str] = None,
    initial_tool_state: Optional[Dict] = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> AgentResult:
    if fast_mode:
        rag_enabled = False
    steps_limit = max_steps or (FAST_MODE_MAX_STEPS if fast_mode else DEFAULT_MAX_STEPS)
    tool_state = _copy_tool_state(initial_tool_state)
    if existing_itinerary:
        _seed_pois_from_itinerary(tool_state, existing_itinerary)
    trace: List[AgentTraceStep] = []

    if mode in ("refine", "single_day") and existing_itinerary and user_request:
        return _run_fast_refine(
            api_key=api_key,
            model=model,
            destination=destination,
            trip_days=trip_days,
            pace=pace,
            interests=interests,
            constraints=constraints,
            user_agent=user_agent,
            mode=mode,
            existing_itinerary=existing_itinerary,
            target_day=target_day,
            user_request=user_request,
            tool_state=tool_state,
            on_progress=on_progress,
        )

    if fast_mode and mode == "generate":
        fast_result = _run_fast_generate(
            api_key=api_key,
            model=model,
            destination=destination,
            trip_days=trip_days,
            pace=pace,
            interests=interests,
            constraints=constraints,
            user_agent=user_agent,
            on_progress=on_progress,
        )
        if fast_result.ok:
            return fast_result
        hard_fail = fast_result.error and any(
            hint in (fast_result.error or "")
            for hint in (
                "Geocoding",
                "Overpass",
                "No POIs matched",
                "Overpass API failed",
            )
        )
        if hard_fail:
            return fast_result
        trace.extend(fast_result.trace)
        _trace_step(
            trace,
            kind="agent",
            name="fast_fallback",
            detail=fast_result.error or "Fast path incomplete",
        )
        if on_progress:
            on_progress("Fast plan incomplete — using tool agent…")
    else:
        _trace_step(
            trace,
            kind="agent",
            name="agent_start",
            detail=f"mode={mode}, fast={fast_mode}, rag={rag_enabled}",
        )

    user_msg = (
        f"Plan a {trip_days}-day trip to {destination}. "
        f"Interests: {', '.join(interests)}. Pace: {pace}."
    )
    if mode != "generate" and user_request:
        user_msg = user_request

    instructions = _build_system_instructions(
        trip_days,
        pace,
        constraints,
        fast_mode,
        mode,
        existing_itinerary,
        target_day,
        user_request,
    )

    client = genai.Client(api_key=api_key)
    contents: List[types.Content] = [
        types.Content(role="user", parts=[types.Part.from_text(text=user_msg)])
    ]
    final_text = ""

    for step in range(steps_limit):
        t0 = time.time()
        if on_progress:
            on_progress(f"Agent step {step + 1}/{steps_limit}: calling Gemini…")

        def _on_gemini_retry(attempt: int, total: int, wait: float, exc: BaseException) -> None:
            trace.append(
                AgentTraceStep(
                    step=step + 1,
                    kind="retry",
                    name="generate_content",
                    duration_ms=0,
                    detail=f"attempt {attempt}/{total} after {exc!s}",
                )
            )
            if on_progress:
                on_progress(
                    f"Gemini temporarily unavailable — retry {attempt}/{total} in {wait:.0f}s…"
                )

        gen_config = types.GenerateContentConfig(
            system_instruction=instructions,
            tools=_gemini_tools(),
        )

        def _one_turn() -> Any:
            _, resp = generate_content_with_fallback(
                client,
                model,
                contents=contents,
                config=gen_config,
                on_progress=on_progress,
            )
            return resp

        try:
            response = call_with_retries(
                "generate_content",
                _one_turn,
                on_retry=_on_gemini_retry,
            )
        except Exception as exc:  # noqa: BLE001
            hint = (
                " (retries exhausted)"
                if is_retryable_error(exc)
                else ""
            )
            return AgentResult(
                ok=False,
                itinerary=None,
                tool_state=tool_state,
                trace=trace,
                error=f"Gemini API error{hint}: {exc}",
            )

        duration = (time.time() - t0) * 1000
        if not response.candidates:
            # Empty candidate blocks are sometimes transient — retry once via progress hook
            empty_retries = 0
            empty_cap = 1 if fast_mode else 2
            while empty_retries < empty_cap and not response.candidates:
                empty_retries += 1
                if on_progress:
                    on_progress(
                        f"Empty Gemini response — retry {empty_retries}/{empty_cap}…"
                    )
                time.sleep(2 ** empty_retries)
                try:
                    response = call_with_retries(
                        "generate_content",
                        _one_turn,
                        on_retry=_on_gemini_retry,
                    )
                except Exception as exc:  # noqa: BLE001
                    return AgentResult(
                        ok=False,
                        itinerary=None,
                        tool_state=tool_state,
                        trace=trace,
                        error=f"Gemini API error: {exc}",
                    )
            if not response.candidates:
                return AgentResult(
                    ok=False,
                    itinerary=None,
                    tool_state=tool_state,
                    trace=trace,
                    error="Gemini returned no candidates after retries.",
                )

        model_content = response.candidates[0].content
        parts = model_content.parts if model_content and model_content.parts else []
        function_calls = [p for p in parts if p.function_call]

        if function_calls:
            contents.append(model_content)
            response_parts: List[types.Part] = []
            for part in function_calls:
                fc = part.function_call
                name = fc.name or ""
                args = _args_to_dict(fc.args)
                t1 = time.time()
                if on_progress:
                    on_progress(f"Running tool: {name}…")
                result = _run_tool(
                    name, args, user_agent, rag_enabled, fast_mode=fast_mode
                )
                if name == "search_pois" and result.get("pois"):
                    _merge_pois(tool_state, result["pois"])
                    if result.get("city_meta"):
                        tool_state["city_meta"] = result["city_meta"]
                if name == "retrieve_guides" and result.get("chunks"):
                    _merge_chunks(tool_state, result["chunks"])
                trace.append(
                    AgentTraceStep(
                        step=step + 1,
                        kind="tool",
                        name=name,
                        duration_ms=(time.time() - t1) * 1000,
                        detail=str(
                            result.get("error")
                            or f"{len(result.get('pois', result.get('chunks', [])))} items"
                        ),
                    )
                )
                response_parts.append(
                    types.Part.from_function_response(name=name, response=result)
                )
            contents.append(types.Content(role="user", parts=response_parts))
            trace.append(
                AgentTraceStep(
                    step=step + 1,
                    kind="model",
                    name="generate_content",
                    duration_ms=duration,
                    detail=f"{len(function_calls)} tool call(s)",
                )
            )
            continue

        final_text = (response.text or "").strip()
        trace.append(
            AgentTraceStep(
                step=step + 1,
                kind="model",
                name="final",
                duration_ms=duration,
                detail="Final response",
            )
        )
        break
    else:
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            error="Agent reached max steps without a final itinerary.",
        )

    if not tool_state["pois"]:
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            raw_final_text=final_text,
            error=(
                "No POIs were collected. For refinements, try naming the place clearly "
                "(e.g. Bharat Mandapam) or regenerate the trip first."
            ),
        )

    parse_attempts = 1 if fast_mode else MAX_RETRIES
    itin, parse_error = _finalize_itinerary(
        final_text,
        tool_state,
        trip_days,
        mode,
        1,
        on_progress,
        trace=trace,
    )
    for parse_attempt in range(1, parse_attempts):
        if itin:
            break
        _trace_step(
            trace,
            kind="validate",
            name="parse_retry",
            detail=f"attempt {parse_attempt + 1}/{parse_attempts}: {parse_error or 'invalid JSON'}",
        )
        if on_progress:
            on_progress(
                f"Invalid itinerary JSON — asking model again ({parse_attempt + 1}/{parse_attempts})…"
            )
        contents.append(
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(
                        text=(
                            "Your last reply was not valid itinerary JSON or used invalid "
                            f"poi_id values. Error: {parse_error}. Reply with ONLY the corrected JSON."
                        )
                    )
                ],
            )
        )
        try:
            response = call_with_retries(
                "generate_content",
                _one_turn,
                on_retry=lambda a, t, w, e: on_progress(f"Gemini retry {a}/{t}…")
                if on_progress
                else None,
            )
            final_text = (response.text or "").strip()
            itin, parse_error = _finalize_itinerary(
                final_text,
                tool_state,
                trip_days,
                mode,
                1,
                on_progress,
                trace=trace,
            )
        except Exception as exc:  # noqa: BLE001
            parse_error = f"Gemini API error during JSON retry: {exc}"
            break

    if parse_error or not itin:
        return AgentResult(
            ok=False,
            itinerary=None,
            tool_state=tool_state,
            trace=trace,
            raw_final_text=final_text,
            error=parse_error or "Invalid itinerary JSON.",
        )

    _postprocess_success(trace, tool_state, destination, user_agent)
    return AgentResult(
        ok=True,
        itinerary=itin,
        tool_state=tool_state,
        trace=trace,
        raw_final_text=final_text,
    )
