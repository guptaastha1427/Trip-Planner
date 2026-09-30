"""
Small retry helper for flaky network / LLM API responses.

What: Runs a callable up to N times with exponential backoff.
Why: Gemini and OSM sometimes return 429/503; users shouldn't see errors on first glitch.
How: Only retries when the error message looks transient (rate limit, timeout, 5xx).
"""

import time
from typing import Callable, Optional, TypeVar

from config import MAX_RETRIES

T = TypeVar("T")

# Substrings that suggest a temporary failure (case-insensitive match on str(exception))
_RETRYABLE_HINTS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "timeout",
    "timed out",
    "resource exhausted",
    "overloaded",
    "unavailable",
    "rate limit",
    "too many requests",
    "connection reset",
    "connection error",
    "temporarily",
)

# Fail fast — retries won't fix auth or bad requests
_NON_RETRYABLE_HINTS = (
    "401",
    "403",
    "invalid api key",
    "api key not valid",
    "permission denied",
    "not found",
    "404",
)


def is_retryable_error(exc: BaseException) -> bool:
    """True if we should backoff and try again."""
    msg = str(exc).lower()
    if any(hint in msg for hint in _NON_RETRYABLE_HINTS):
        return False
    return any(hint in msg for hint in _RETRYABLE_HINTS)


def call_with_retries(
    operation: str,
    fn: Callable[[], T],
    *,
    max_attempts: int = MAX_RETRIES,
    on_retry: Optional[Callable[[int, int, float, BaseException], None]] = None,
) -> T:
    """
    Call fn(); on retryable errors sleep 2**attempt seconds and retry.

    on_retry(attempt_number, max_attempts, sleep_seconds, exception) updates UI/logs.
    """
    last_error: Optional[BaseException] = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            is_last = attempt >= max_attempts - 1
            if is_last or not is_retryable_error(exc):
                raise
            sleep_sec = 2 ** attempt
            if on_retry:
                on_retry(attempt + 1, max_attempts, sleep_sec, exc)
            time.sleep(sleep_sec)
    if last_error:
        raise last_error
    raise RuntimeError(f"{operation} failed with no result")
