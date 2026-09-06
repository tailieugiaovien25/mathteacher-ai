from __future__ import annotations

import os
from collections.abc import Mapping

from document_intelligence.ai_provider import (
    AIDocumentAnalyzer,
)
from document_intelligence.deterministic_analyzer import (
    DeterministicDocumentAnalyzer,
)
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


def _resolve_provider_credential(
    *,
    provider_id: str,
    credentials: Mapping[str, str] | None,
) -> str | None:
    """Resolve one transient provider credential without persisting it."""
    normalized = provider_id.strip().lower()

    if credentials is not None:
        candidate = credentials.get(normalized)

        if isinstance(candidate, str):
            candidate = candidate.strip()

            if candidate:
                return candidate

    if normalized == "openai":
        return os.getenv("OPENAI_API_KEY")

    if normalized == "gemini":
        return os.getenv("GEMINI_API_KEY")

    return None


def _build_ai_provider(
    *,
    provider_id: str,
    model: str | None,
    credentials: Mapping[str, str] | None = None,
):
    normalized = provider_id.strip().lower()

    if normalized == "openai":
        api_key = _resolve_provider_credential(
            provider_id=normalized,
            credentials=credentials,
        )

        if not api_key:
            return None

        return OpenAIDocumentProvider(
            api_key=api_key,
            model=model,
        )

    if normalized == "gemini":
        api_key = _resolve_provider_credential(
            provider_id=normalized,
            credentials=credentials,
        )

        if not api_key:
            return None

        return GeminiDocumentProvider(
            api_key=api_key,
            model=model,
        )

    return None


def build_document_analyzer(
    *,
    config: (
        DocumentIntelligenceRuntimeConfig
        | None
    ) = None,
    credentials: Mapping[str, str] | None = None,
):
    resolved = (
        config
        or DocumentIntelligenceRuntimeConfig
        .from_environment()
    )

    deterministic = (
        DeterministicDocumentAnalyzer()
    )

    if not resolved.ai_enabled:
        return HybridDocumentAnalyzer(
            deterministic_analyzer=deterministic,
            ai_analyzer=None,
        )

    try:
        provider = _build_ai_provider(
            provider_id=resolved.provider,
            model=resolved.model,
            credentials=credentials,
        )

        if provider is None:
            return HybridDocumentAnalyzer(
                deterministic_analyzer=deterministic,
                ai_analyzer=None,
            )

        ai_analyzer = AIDocumentAnalyzer(
            provider=provider
        )

    except Exception:
        return HybridDocumentAnalyzer(
            deterministic_analyzer=deterministic,
            ai_analyzer=None,
        )

    return HybridDocumentAnalyzer(
        deterministic_analyzer=deterministic,
        ai_analyzer=ai_analyzer,
    )
