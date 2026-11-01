"""Timed agent trace spans — record full duration even on failure."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Callable, List, Optional

from services.trip.agent_trace import AgentTraceStep

TraceCallback = Optional[Callable[[List[AgentTraceStep]], None]]


def _next_step_no(trace: List[AgentTraceStep]) -> int:
    return (max((s.step for s in trace), default=0) + 1) if trace else 1


def notify_trace(trace: List[AgentTraceStep], on_trace: TraceCallback) -> None:
    if on_trace:
        on_trace(list(trace))


@contextmanager
def trace_span(
    trace: List[AgentTraceStep],
    *,
    kind: str,
    name: str,
    start_detail: str = "running…",
    on_trace: TraceCallback = None,
):
    """
    Append a running step, then set duration_ms in ``finally`` (success or failure).
    Call ``set_detail("…")`` before exit to replace the final detail line.
    """
    t0 = time.time()
    idx = len(trace)
    trace.append(
        AgentTraceStep(
            step=_next_step_no(trace),
            kind=kind,
            name=name,
            duration_ms=0.0,
            detail=start_detail,
            started_at=t0,
        )
    )
    notify_trace(trace, on_trace)
    final_detail: List[str] = [start_detail]

    def set_detail(msg: str) -> None:
        final_detail[0] = msg

    try:
        yield set_detail
    finally:
        ms = (time.time() - t0) * 1000
        if idx < len(trace):
            trace[idx].duration_ms = ms
            trace[idx].detail = final_detail[0]
        notify_trace(trace, on_trace)


def effective_duration_ms(step: AgentTraceStep, *, now: Optional[float] = None) -> float:
    """Use recorded duration, or elapsed time since ``started_at`` for in-flight steps."""
    if step.duration_ms and step.duration_ms > 0:
        return float(step.duration_ms)
    started = float(getattr(step, "started_at", 0) or 0)
    if started and now:
        return max(0.0, (now - started) * 1000)
    return float(step.duration_ms or 0)
