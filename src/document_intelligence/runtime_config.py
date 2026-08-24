from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DocumentIntelligenceRuntimeConfig:
    ai_enabled: bool = False
    provider: str = "openai"
    model: str | None = None

    @classmethod
    def from_environment(
        cls,
    ) -> "DocumentIntelligenceRuntimeConfig":
        enabled_raw = os.getenv(
            "DOCUMENT_AI_ENABLED",
            "",
        )

        enabled = (
            enabled_raw.strip().casefold()
            in {
                "1",
                "true",
                "yes",
                "on",
            }
        )

        provider = (
            os.getenv(
                "DOCUMENT_AI_PROVIDER",
                "openai",
            )
            .strip()
            .casefold()
        )

        model = os.getenv(
            "OPENAI_DOCUMENT_MODEL"
        )

        if model is not None:
            model = model.strip() or None

        return cls(
            ai_enabled=enabled,
            provider=provider,
            model=model,
        )
