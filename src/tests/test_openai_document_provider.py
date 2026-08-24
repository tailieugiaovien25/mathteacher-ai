import json

import pytest

from document_intelligence.contracts import (
    DocumentField,
)
from document_intelligence.openai_provider import (
    OpenAIDocumentProvider,
)


class FakeResponse:
    def __init__(
        self,
        payload,
    ):
        self.output_text = json.dumps(
            payload,
            ensure_ascii=False,
        )


class FakeResponsesAPI:
    def __init__(
        self,
        payload,
    ):
        self.payload = payload
        self.calls = []

    def create(
        self,
        **kwargs,
    ):
        self.calls.append(kwargs)

        return FakeResponse(
            self.payload
        )


class FakeClient:
    def __init__(
        self,
        payload,
    ):
        self.responses = FakeResponsesAPI(
            payload
        )


def test_openai_provider_converts_structured_output():
    client = FakeClient(
        {
            "candidates": [
                {
                    "field": "lesson_title",
                    "value": "Đơn thức",
                    "confidence": 0.94,
                    "evidence": (
                        "TIẾT 1 - §1: ĐƠN THỨC"
                    ),
                },
            ],
        }
    )

    provider = OpenAIDocumentProvider(
        client=client,
        model="test-model",
    )

    result = provider.analyze(
        document_text="sample"
    )

    assert len(result) == 1

    candidate = result[0]

    assert (
        candidate.field
        is DocumentField.LESSON_TITLE
    )
    assert candidate.value == "Đơn thức"
    assert candidate.confidence == 0.94


def test_openai_provider_uses_responses_api():
    client = FakeClient(
        {
            "candidates": [],
        }
    )

    provider = OpenAIDocumentProvider(
        client=client,
        model="test-model",
    )

    provider.analyze(
        document_text="sample"
    )

    assert len(
        client.responses.calls
    ) == 1

    call = client.responses.calls[0]

    assert call["model"] == "test-model"

    assert (
        call["text"]["format"]["type"]
        == "json_schema"
    )

    assert (
        call["text"]["format"]["strict"]
        is True
    )


def test_empty_document_does_not_call_api():
    client = FakeClient(
        {
            "candidates": [],
        }
    )

    provider = OpenAIDocumentProvider(
        client=client,
    )

    result = provider.analyze(
        document_text="   "
    )

    assert result == ()
    assert client.responses.calls == []


def test_missing_api_key_is_rejected(
    monkeypatch,
):
    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="OPENAI_API_KEY",
    ):
        OpenAIDocumentProvider()


def test_model_can_come_from_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "OPENAI_DOCUMENT_MODEL",
        "custom-model",
    )

    client = FakeClient(
        {
            "candidates": [],
        }
    )

    provider = OpenAIDocumentProvider(
        client=client,
    )

    provider.analyze(
        document_text="sample"
    )

    call = client.responses.calls[0]

    assert (
        call["model"]
        == "custom-model"
    )
