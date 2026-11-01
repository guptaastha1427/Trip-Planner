"""
Shared HTTP helpers with retries, rate limiting, and User-Agent headers.

What: Wraps requests.get/post for Nominatim, Overpass, and Wikivoyage.
Why: OSM requires identifying User-Agent; production apps need backoff on 429/5xx.
How: Exponential sleep on rate limits; raises after MAX_RETRIES failures.
"""

import time
from typing import Any, Dict, Optional, Sequence

import requests

from config import (
    MAX_RETRIES,
    OVERPASS_MAX_RETRIES,
    REQUEST_TIMEOUT_SEC,
    get_overpass_timeout_sec,
    get_overpass_urls,
)

# Nominatim policy: max 1 request per second per application
_last_nominatim_call: float = 0.0
NOMINATIM_MIN_INTERVAL_SEC = 1.05


def build_headers(user_agent: str) -> Dict[str, str]:
    """OSM and Wikimedia APIs require a descriptive User-Agent with contact info."""
    return {"User-Agent": user_agent, "Accept": "application/json"}


def _respect_nominatim_rate_limit() -> None:
    """Sleep if we called Nominatim too recently (global throttle for this process)."""
    global _last_nominatim_call
    elapsed = time.time() - _last_nominatim_call
    if elapsed < NOMINATIM_MIN_INTERVAL_SEC:
        time.sleep(NOMINATIM_MIN_INTERVAL_SEC - elapsed)
    _last_nominatim_call = time.time()


def get_json(
    url: str,
    user_agent: str,
    params: Optional[Dict[str, Any]] = None,
    *,
    use_nominatim_limit: bool = False,
) -> Any:
    """
    GET JSON with retries. use_nominatim_limit=True enforces 1 req/sec for geocoding.
    """
    headers = build_headers(user_agent)
    last_error: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            if use_nominatim_limit:
                _respect_nominatim_rate_limit()
            response = requests.get(
                url, headers=headers, params=params, timeout=REQUEST_TIMEOUT_SEC
            )
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 — capstone asks for broad API error handling
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Request failed after retries: {last_error}")


def post_text(
    url: str,
    user_agent: str,
    data: str,
) -> str:
    """POST (Overpass uses form body) with the same retry pattern."""
    headers = build_headers(user_agent)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    last_error: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            # Overpass expects the query in a form field named `data`.
            response = requests.post(
                url,
                headers=headers,
                data={"data": data},
                timeout=REQUEST_TIMEOUT_SEC,
            )
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)

    raise RuntimeError(f"POST failed after retries: {last_error}")


_OVERPASS_RETRYABLE_STATUS = frozenset({429, 502, 503, 504})


def post_overpass(user_agent: str, data: str, *, urls: Optional[Sequence[str]] = None) -> str:
    """
    POST an Overpass QL query; try mirror endpoints and retry transient 5xx/429.
    """
    headers = build_headers(user_agent)
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    endpoints = list(urls or get_overpass_urls())
    failures: list[str] = []
    timeout = get_overpass_timeout_sec()

    for url in endpoints:
        last_error: Optional[Exception] = None
        for attempt in range(OVERPASS_MAX_RETRIES):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    data={"data": data},
                    timeout=timeout,
                )
                if response.status_code in _OVERPASS_RETRYABLE_STATUS:
                    last_error = requests.HTTPError(
                        f"{response.status_code} Server Error for url: {url}",
                        response=response,
                    )
                    time.sleep(min(8, 2 ** attempt + 1))
                    continue
                response.raise_for_status()
                return response.text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt == OVERPASS_MAX_RETRIES - 1:
                    break
                time.sleep(min(8, 2 ** attempt + 1))
        failures.append(f"{url}: {last_error}")

    detail = "; ".join(failures) if failures else "unknown error"
    raise RuntimeError(f"Overpass API failed after {len(endpoints)} endpoint(s): {detail}")
