from __future__ import annotations

from document_intelligence import runtime_factory as factory
from document_intelligence.runtime_config import DocumentIntelligenceRuntimeConfig


def _enabled(provider: str) -> DocumentIntelligenceRuntimeConfig:
    return DocumentIntelligenceRuntimeConfig(
        ai_enabled=True,
        provider=provider,
        model="test-model",
    )


def test_gemini_transient_credential_without_environment(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    captured = {}

    def fake_provider(*, api_key, model):
        captured["api_key"] = api_key
        captured["model"] = model
        return object()

    monkeypatch.setattr(factory, "GeminiDocumentProvider", fake_provider)

    provider = factory._build_ai_provider(
        provider_id="gemini",
        model="gemini-test",
        credentials={"gemini": " transient-gemini-key "},
    )

    assert provider is not None
    assert captured == {
        "api_key": "transient-gemini-key",
        "model": "gemini-test",
    }


def test_openai_transient_credential_without_environment(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    captured = {}

    def fake_provider(*, api_key, model):
        captured["api_key"] = api_key
        captured["model"] = model
        return object()

    monkeypatch.setattr(factory, "OpenAIDocumentProvider", fake_provider)

    provider = factory._build_ai_provider(
        provider_id="openai",
        model="openai-test",
        credentials={"openai": " transient-openai-key "},
    )

    assert provider is not None
    assert captured == {
        "api_key": "transient-openai-key",
        "model": "openai-test",
    }


def test_transient_credential_precedes_environment(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "environment-key")

    assert factory._resolve_provider_credential(
        provider_id="gemini",
        credentials={"gemini": "transient-key"},
    ) == "transient-key"


def test_blank_transient_keeps_environment_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "environment-key")

    assert factory._resolve_provider_credential(
        provider_id="gemini",
        credentials={"gemini": "   "},
    ) == "environment-key"


def test_existing_environment_behavior_preserved(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-environment-key")

    assert factory._resolve_provider_credential(
        provider_id="openai",
        credentials=None,
    ) == "legacy-environment-key"


def test_unknown_provider_has_no_credential(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    assert factory._resolve_provider_credential(
        provider_id="unknown-provider",
        credentials={
            "gemini": "transient-gemini",
            "openai": "transient-openai",
        },
    ) is None


def test_build_document_analyzer_forwards_credentials(monkeypatch):
    captured = {}

    class FakeProvider:
        def analyze(self, *, document_text: str):
            return ()

    def fake_build_ai_provider(*, provider_id, model, credentials=None):
        captured["provider_id"] = provider_id
        captured["model"] = model
        captured["credentials"] = credentials
        return FakeProvider()

    monkeypatch.setattr(
        factory,
        "_build_ai_provider",
        fake_build_ai_provider,
    )

    credentials = {"gemini": "transient-key"}

    analyzer = factory.build_document_analyzer(
        config=_enabled("gemini"),
        credentials=credentials,
    )

    assert analyzer is not None
    assert captured == {
        "provider_id": "gemini",
        "model": "test-model",
        "credentials": credentials,
    }


def test_disabled_ai_does_not_construct_provider(monkeypatch):
    def forbidden_build(**kwargs):
        raise AssertionError(
            "provider must not be constructed when AI is disabled"
        )

    monkeypatch.setattr(
        factory,
        "_build_ai_provider",
        forbidden_build,
    )

    analyzer = factory.build_document_analyzer(
        config=DocumentIntelligenceRuntimeConfig(
            ai_enabled=False,
            provider="gemini",
            model="test-model",
        ),
        credentials={"gemini": "must-not-be-used"},
    )

    assert analyzer is not None


def test_credentials_mapping_is_not_mutated():
    credentials = {"gemini": "temporary-value"}
    before = dict(credentials)

    factory._resolve_provider_credential(
        provider_id="gemini",
        credentials=credentials,
    )

    assert credentials == before


def test_runtime_factory_remains_streamlit_independent():
    with open(factory.__file__, "r", encoding="utf-8") as handle:
        text = handle.read().lower()

    assert "import streamlit" not in text
    assert "st.secrets" not in text
