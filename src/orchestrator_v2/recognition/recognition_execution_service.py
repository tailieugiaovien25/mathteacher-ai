from __future__ import annotations

from typing import Any

from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)


class RecognitionExecutionService:
    """
    V2 Recognition Execution Service.

    Responsibility:
    - Resolve a recognition provider through the configured resolver.
    - Execute the resolved provider's recognize() contract.
    - Return recognition evidence exactly as produced by the provider.

    This component MUST NOT:
    - access the provider registry directly;
    - create a final RecognitionResult;
    - create Identity;
    - create new Data Types;
    - modify Registry or Rule state;
    - dispatch processors;
    - mutate input data;
    - provide hidden fallback providers.
    """

    def __init__(self, provider_resolver: Any) -> None:
        if provider_resolver is None:
            raise ValueError("provider_resolver is required")

        self._provider_resolver = provider_resolver

    def execute(
        self,
        provider_id: str,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[RecognitionEvidence, ...]:
        """
        Resolve and execute exactly one recognition provider.
        """

        provider = self._provider_resolver.resolve(provider_id)

        return provider.recognize(
            data,
            context=context,
        )