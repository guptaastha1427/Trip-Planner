"""Deterministic checks on generated policy answers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Sequence


def keywords_present(text: str, keywords: Sequence[str]) -> bool:
    low = (text or "").lower()
    for kw in keywords:
        if kw and kw.lower() not in low:
            return False
    return True


def has_citation_markup(reply: str) -> bool:
    return "rag-inline-cite" in (reply or "")


def mentions_terms_source(reply: str) -> bool:
    low = (reply or "").lower()
    return "terms" in low or "policies" in low


def package_math_hints(reply: str) -> List[str]:
    """Return list of missing required tokens for package pricing answers (heuristic)."""
    missing: List[str] = []
    low = (reply or "").lower()
    if "1200" not in reply and "1,200" not in reply:
        if any(w in low for w in ("night", "add-on", "extra night")):
            missing.append("night_add_on_rate")
    if "1.12" in low or "12%" in low:
        if "flex" not in low:
            missing.append("flex_label")
    return missing


def generation_code_score(
    reply: str,
    *,
    expected_keywords: Sequence[str],
    require_citation: bool = True,
) -> Dict[str, Any]:
    checks = {
        "keywords_ok": keywords_present(reply, expected_keywords) if expected_keywords else True,
        "citation_ok": has_citation_markup(reply) if require_citation else True,
        "terms_attribution_ok": mentions_terms_source(reply),
        "package_math_gaps": package_math_hints(reply),
    }
    checks["passed"] = (
        checks["keywords_ok"]
        and checks["citation_ok"]
        and checks["terms_attribution_ok"]
        and not checks["package_math_gaps"]
    )
    return checks


def no_forbidden_inventory_claims(text: str) -> bool:
    """Trip/travel hints should not claim live seat availability."""
    bad = re.compile(
        r"\b(seats available|booked on flight [A-Z]{2}\d+|confirmed reservation on)\b",
        re.I,
    )
    return bad.search(text or "") is None
