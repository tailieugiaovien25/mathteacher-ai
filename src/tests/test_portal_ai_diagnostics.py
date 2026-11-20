from __future__ import annotations

import logging
from urllib.error import HTTPError, URLError

from portal_v2.ai_diagnostics import (
    classify_ai_failure,
    log_teaching_assistant_failure,
)


def test_classifies_http_status_from_wrapped_provider_error():
    cause = HTTPError("https://example.invalid/api/chat", 401, "unauthorized", {}, None)
    try:
        raise RuntimeError("provider request failed") from cause
    except RuntimeError as exc:
        assert classify_ai_failure(exc) == "http_401"


def test_classifies_network_timeout_and_unknown_failures():
    assert classify_ai_failure(URLError("private endpoint detail")) == "network_error"
    assert classify_ai_failure(TimeoutError("private timeout detail")) == "timeout"
    assert classify_ai_failure(RuntimeError("unexpected private detail")) == "unexpected_error"


def test_logs_correlation_and_safe_metadata_without_exception_text(caplog):
    secret = "OLLAMA_API_KEY_DO_NOT_LOG"
    prompt = "PRIVATE_STUDENT_PROMPT_DO_NOT_LOG"
    caplog.set_level(logging.ERROR, logger="mathteacher_ai.teaching_assistant")

    request_id = log_teaching_assistant_failure(
        RuntimeError(f"{secret} {prompt}"),
        mode="student",
    )

    assert len(request_id) == 12
    assert request_id in caplog.text
    assert "mode=student" in caplog.text
    assert "failure=unexpected_error" in caplog.text
    assert secret not in caplog.text
    assert prompt not in caplog.text
