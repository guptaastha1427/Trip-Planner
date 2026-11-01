"""Reusable travel nav chip markup (pairs with .tp-nav-chip* in ui_travel_theme)."""

from __future__ import annotations

import html
from typing import Iterable, Sequence, Tuple

ChipSpec = Tuple[str, bool]


def nav_chip_html(label: str, *, active: bool = False) -> str:
    safe = html.escape(label.strip())
    state = " tp-nav-chip--active" if active else ""
    return f'<span class="tp-nav-chip{state}">{safe}</span>'


def nav_chip_row_html(chips: Sequence[ChipSpec]) -> str:
    items = "".join(nav_chip_html(label, active=on) for label, on in chips)
    return f'<nav class="tp-nav-chip-row" aria-label="Sections">{items}</nav>'


def nav_chip_row_from_labels(labels: Iterable[str], *, active_index: int = 0) -> str:
    specs = [(lbl, i == active_index) for i, lbl in enumerate(labels)]
    return nav_chip_row_html(specs)
