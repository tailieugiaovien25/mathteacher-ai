from document_intelligence import (
    DocumentIntelligenceRuntimeConfig,
    HybridDocumentAnalyzer,
    build_document_analyzer,
)


def test_config_defaults_to_ai_disabled(
    monkeypatch,
):
    monkeypatch.delenv(
        "DOCUMENT_AI_ENABLED",
        raising=False,
    )

    config = (
        DocumentIntelligenceRuntimeConfig
        .from_environment()
    )

    assert config.ai_enabled is False
    assert config.provider == "openai"


def test_config_reads_enabled_flag(
    monkeypatch,
):
    monkeypatch.setenv(
        "DOCUMENT_AI_ENABLED",
        "true",
    )

    config = (
        DocumentIntelligenceRuntimeConfig
        .from_environment()
    )

    assert config.ai_enabled is True


def test_runtime_without_ai_key_still_builds(
    monkeypatch,
):
    monkeypatch.setenv(
        "DOCUMENT_AI_ENABLED",
        "true",
    )

    monkeypatch.delenv(
        "OPENAI_API_KEY",
        raising=False,
    )

    analyzer = build_document_analyzer()

    assert isinstance(
        analyzer,
        HybridDocumentAnalyzer,
    )


def test_runtime_ai_disabled_builds_hybrid(
    monkeypatch,
):
    monkeypatch.setenv(
        "DOCUMENT_AI_ENABLED",
        "false",
    )

    analyzer = build_document_analyzer()

    assert isinstance(
        analyzer,
        HybridDocumentAnalyzer,
    )


def test_unknown_provider_falls_back_safely(
    monkeypatch,
):
    monkeypatch.setenv(
        "DOCUMENT_AI_ENABLED",
        "true",
    )

    monkeypatch.setenv(
        "DOCUMENT_AI_PROVIDER",
        "unknown-provider",
    )

    analyzer = build_document_analyzer()

    assert isinstance(
        analyzer,
        HybridDocumentAnalyzer,
    )


def test_config_reads_model(
    monkeypatch,
):
    monkeypatch.setenv(
        "OPENAI_DOCUMENT_MODEL",
        "custom-model",
    )

    config = (
        DocumentIntelligenceRuntimeConfig
        .from_environment()
    )

    assert (
        config.model
        == "custom-model"
    )


def test_runtime_without_ai_can_analyze_text(
    monkeypatch,
):
    monkeypatch.setenv(
        "DOCUMENT_AI_ENABLED",
        "false",
    )

    analyzer = build_document_analyzer()

    result = analyzer.analyze(
        document_text=(
            "Tên bài: Đơn thức"
        )
    )

    assert result.ai_used is False

    assert (
        result.analysis.proposals
    )
