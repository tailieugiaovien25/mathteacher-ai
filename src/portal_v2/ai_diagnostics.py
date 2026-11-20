"""Safe, privacy-preserving diagnostics for Teaching Assistant failures.

Only allowlisted metadata is logged. Exception messages, request prompts,
conversation history, URLs, response bodies, and credentials are never logged.
"""
from __future__ import annotations

import logging
import uuid
from urllib.error import HTTPError, URLError

_LOGGER = logging.getLogger("mathteacher_ai.teaching_assistant")


def _exception_chain(exc: BaseException):
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def classify_ai_failure(exc: BaseException) -> str:
    """Return a low-cardinality failure code without exposing exception text."""
    for item in _exception_chain(exc):
        if isinstance(item, HTTPError):
            code = int(item.code)
            return f"http_{code}" if 100 <= code <= 599 else "http_error"
        if isinstance(item, TimeoutError):
            return "timeout"
        if isinstance(item, URLError):
            return "network_error"
    return "unexpected_error"


def log_teaching_assistant_failure(exc: BaseException, *, mode: str) -> str:
    """Log safe diagnostic metadata and return a correlation ID for support."""
    request_id = uuid.uuid4().hex[:12]
    safe_mode = mode if mode in {"teacher", "student"} else "unknown"
    _LOGGER.error(
        "Teaching Assistant request failed request_id=%s mode=%s failure=%s exception_type=%s",
        request_id,
        safe_mode,
        classify_ai_failure(exc),
        type(exc).__name__,
    )
    return request_id
