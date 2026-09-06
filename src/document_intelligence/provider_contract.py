from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderDescriptor:
    """Non-secret metadata describing a registered AI provider."""

    provider_id: str
    display_name: str
    supports_document_intelligence: bool = True
    supports_lesson_authoring: bool = False
    configurable_model: bool = True

    def __post_init__(self) -> None:
        normalized = self.provider_id.strip().lower()

        if not normalized:
            raise ValueError(
                "provider_id must not be empty"
            )

        if normalized != self.provider_id:
            raise ValueError(
                "provider_id must already be normalized lowercase text"
            )

        if not self.display_name.strip():
            raise ValueError(
                "display_name must not be empty"
            )
