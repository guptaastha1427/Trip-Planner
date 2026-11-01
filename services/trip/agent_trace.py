"""Shared agent trace step type (no imports from agent.py)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentTraceStep:
    step: int
    kind: str
    name: str
    duration_ms: float
    detail: str
    started_at: float = 0.0
