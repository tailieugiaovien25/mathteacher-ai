from __future__ import annotations

from document_intelligence.gemini_provider import (
    GeminiDocumentProvider,
)
from document_intelligence.hybrid_analyzer import (
    HybridDocumentAnalyzer,
)
from document_intelligence.openai_provider import (
    OpenAIDocumentProvider,
)
from document_intelligence.runtime_config import (
    DocumentIntelligenceRuntimeConfig,
)
from document_intelligence.runtime_factory import (
    _build_ai_provider,
    build_document_analyzer,
)


def _config(
    *,
    enabled: bool,
    provider: str,
    model: str | None = None,
) -> DocumentIntelligenceRuntimeConfig:
    return DocumentIntelligenceRuntimeConfig(
        ai_enabled=enabled,
        provider=provider,
        model=model,
    )


def test_ai_disabled_keeps_deterministic_only(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "openai-test",
    )
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "gemini-test",
    )

    analyzer = build_document_analyzer(
        config=_config(
            enabled=False,
            provider="gemini",
        )
    )

    assert isinstance(
        analyzer,
        HybridDocumentAnalyzer,
    )
    assert analyzer._ai_analyzer is None


def test_unknown_provider_falls_back_safely() -> None:
    analyzer = build_document_analyzer(
        config=_config(
            enabled=True,
            provider="unknown-provider",
        )
    )

    assert isinstance(
        analyzer,
        HybridDocumentAnalyzer,
    )
    assert analyzer._ai_analyzer is None


def test_openai_without_key_falls_back(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False,
    )

    analyzer = build_document_analyzer(
        config=_config(
            enabled=True,
            provider="openai",
        )
    )

    assert analyzer._ai_analyzer is None


def test_gemini_without_key_falls_back(
    monkeypatch,
) -> None:
    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )

    analyzer = build_document_analyzer(
        config=_config(
            enabled=True,
            provider="gemini",
        )
    )

    assert analyzer._ai_analyzer is None


def test_build_provider_returns_openai(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-openai-key",
    )

    provider = _build_ai_provider(
        provider_id="openai",
        model="test-openai-model",
    )

    assert isinstance(
        provider,
        OpenAIDocumentProvider,
    )


def test_build_provider_returns_gemini(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-gemini-key",
    )

    provider = _build_ai_provider(
        provider_id="gemini",
        model="test-gemini-model",
    )

    assert isinstance(
        provider,
        GeminiDocumentProvider,
    )
    assert provider.model == "test-gemini-model"


def test_provider_id_is_case_insensitive(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-gemini-key",
    )

    provider = _build_ai_provider(
        provider_id=" Gemini ",
        model="test-model",
    )

    assert isinstance(
        provider,
        GeminiDocumentProvider,
    )


def test_unknown_provider_returns_none() -> None:
    assert (
        _build_ai_provider(
            provider_id="future-ai",
            model=None,
        )
        is None
    )


def test_gemini_constructor_failure_falls_back(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-gemini-key",
    )

    import document_intelligence.runtime_factory as factory

    class BrokenGemini:
        def __init__(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        factory,
        "GeminiDocumentProvider",
        BrokenGemini,
    )

    analyzer = factory.build_document_analyzer(
        config=_config(
            enabled=True,
            provider="gemini",
        )
    )

    assert analyzer._ai_analyzer is None


def test_openai_constructor_failure_falls_back(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "OPENAI_API_KEY",
        "test-openai-key",
    )

    import document_intelligence.runtime_factory as factory

    class BrokenOpenAI:
        def __init__(self, **kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        factory,
        "OpenAIDocumentProvider",
        BrokenOpenAI,
    )

    analyzer = factory.build_document_analyzer(
        config=_config(
            enabled=True,
            provider="openai",
        )
    )

    assert analyzer._ai_analyzer is None
