from __future__ import annotations

import os

from document_intelligence.ai_provider import (
    AIDocumentAnalyzer,
)
from document_intelligence.deterministic_analyzer import (
    DeterministicDocumentAnalyzer,
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


def build_document_analyzer(
    *,
    config: (
        DocumentIntelligenceRuntimeConfig
        | None
    ) = None,
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

    if resolved.provider != "openai":
        return HybridDocumentAnalyzer(
            deterministic_analyzer=deterministic,
            ai_analyzer=None,
        )

    api_key = os.getenv(
        "OPENAI_API_KEY"
    )

    if not api_key:
        return HybridDocumentAnalyzer(
            deterministic_analyzer=deterministic,
            ai_analyzer=None,
        )

    try:
        provider = OpenAIDocumentProvider(
            api_key=api_key,
            model=resolved.model,
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
