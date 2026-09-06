from __future__ import annotations

import json

import pytest

from document_intelligence.ai_provider import (
    AIDocumentAnalyzer,
    AIFieldCandidate,
)
from document_intelligence.contracts import DocumentField
from document_intelligence.gemini_provider import (
    GeminiDocumentProvider,
    GeminiDocumentProviderError,
)


def _response(*, candidates: list[dict]) -> dict:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {"candidates": candidates}
                            )
                        }
                    ]
                }
            }
        ]
    }


def test_empty_document_returns_empty_tuple() -> None:
    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=lambda *args: {},
    )
    assert provider.analyze(document_text="   ") == ()


def test_provider_returns_canonical_candidate() -> None:
    field = next(iter(DocumentField))

    def transport(url, headers, payload, timeout):
        return _response(
            candidates=[
                {
                    "field": field.value,
                    "value": "Example",
                    "confidence": 0.90,
                    "evidence": "Evidence",
                }
            ]
        )

    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=transport,
    )

    result = provider.analyze(
        document_text="Lesson document"
    )

    assert len(result) == 1
    assert isinstance(result[0], AIFieldCandidate)
    assert result[0].field == field
    assert result[0].value == "Example"


def test_gemini_runs_through_existing_ai_document_analyzer() -> None:
    field = next(iter(DocumentField))

    def transport(url, headers, payload, timeout):
        return _response(
            candidates=[
                {
                    "field": field.value,
                    "value": "Canonical value",
                    "confidence": 0.95,
                    "evidence": "Document evidence",
                }
            ]
        )

    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=transport,
    )

    analyzer = AIDocumentAnalyzer(
        provider=provider
    )

    analysis = analyzer.analyze(
        document_text="Lesson document"
    )

    assert len(analysis.proposals) == 1

    proposal = analysis.proposals[0]

    assert proposal.field == field
    assert proposal.value == "Canonical value"
    assert proposal.confidence == 0.95
    assert proposal.evidence == "Document evidence"


def test_api_key_is_not_written_into_payload() -> None:
    captured = {}

    def transport(url, headers, payload, timeout):
        captured["headers"] = dict(headers)
        captured["payload"] = payload
        return _response(candidates=[])

    provider = GeminiDocumentProvider(
        api_key="secret-test-key",
        transport=transport,
    )

    provider.analyze(document_text="Document")

    assert (
        captured["headers"]["x-goog-api-key"]
        == "secret-test-key"
    )

    assert (
        "secret-test-key"
        not in json.dumps(captured["payload"])
    )


def test_selected_model_is_used() -> None:
    captured = {}

    def transport(url, headers, payload, timeout):
        captured["url"] = url
        return _response(candidates=[])

    provider = GeminiDocumentProvider(
        api_key="test-key",
        model="gemini-test-model",
        transport=transport,
    )

    provider.analyze(document_text="Document")

    assert "gemini-test-model" in captured["url"]


def test_json_mime_type_is_requested() -> None:
    captured = {}

    def transport(url, headers, payload, timeout):
        captured["payload"] = payload
        return _response(candidates=[])

    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=transport,
    )

    provider.analyze(document_text="Document")

    assert (
        captured["payload"]
        ["generationConfig"]
        ["responseMimeType"]
        == "application/json"
    )


def test_unknown_field_is_ignored() -> None:
    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=lambda *args: _response(
            candidates=[
                {
                    "field": "unknown-field",
                    "value": "Value",
                    "confidence": 0.9,
                    "evidence": "",
                }
            ]
        ),
    )

    assert provider.analyze(
        document_text="Document"
    ) == ()


def test_invalid_confidence_is_ignored() -> None:
    field = next(iter(DocumentField))

    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=lambda *args: _response(
            candidates=[
                {
                    "field": field.value,
                    "value": "Value",
                    "confidence": 2.0,
                    "evidence": "",
                }
            ]
        ),
    )

    assert provider.analyze(
        document_text="Document"
    ) == ()


def test_invalid_json_is_rejected() -> None:
    response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "not-json"}
                    ]
                }
            }
        ]
    }

    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=lambda *args: response,
    )

    with pytest.raises(GeminiDocumentProviderError):
        provider.analyze(document_text="Document")


def test_missing_response_text_is_rejected() -> None:
    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=lambda *args: {},
    )

    with pytest.raises(GeminiDocumentProviderError):
        provider.analyze(document_text="Document")


def test_missing_api_key_is_rejected(monkeypatch) -> None:
    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    with pytest.raises(ValueError):
        GeminiDocumentProvider()


def test_transport_error_is_wrapped() -> None:
    def broken_transport(url, headers, payload, timeout):
        raise RuntimeError("boom")

    provider = GeminiDocumentProvider(
        api_key="test-key",
        transport=broken_transport,
    )

    with pytest.raises(GeminiDocumentProviderError):
        provider.analyze(document_text="Document")
