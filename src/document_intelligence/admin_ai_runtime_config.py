from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from document_intelligence.runtime_config import (
    DocumentIntelligenceRuntimeConfig,
)


AI_RUNTIME_SECTION = "ai_runtime"

SUPPORTED_PROVIDERS = frozenset(
    {
        "gemini",
        "openai",
    }
)


def _bool_value(
    value: Any,
    *,
    default: bool = False,
) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value == 1

    if isinstance(value, str):
        normalized = value.strip().casefold()

        if normalized in {
            "1",
            "true",
            "yes",
            "on",
            "enabled",
        }:
            return True

        if normalized in {
            "0",
            "false",
            "no",
            "off",
            "disabled",
        }:
            return False

    return default


def _text_value(
    value: Any,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        return None

    normalized = value.strip()

    return normalized or None


@dataclass(frozen=True)
class AdminAIRuntimeConfiguration:
    """Validated, secret-free AI configuration selected by ADMIN."""

    enabled: bool = False
    provider: str = "openai"
    model: str | None = None

    @classmethod
    def disabled(
        cls,
    ) -> "AdminAIRuntimeConfiguration":
        return cls(
            enabled=False,
            provider="openai",
            model=None,
        )

    @classmethod
    def from_configuration_payload(
        cls,
        payload: Mapping[str, Any] | None,
    ) -> "AdminAIRuntimeConfiguration":
        if not isinstance(payload, Mapping):
            return cls.disabled()

        section = payload.get(
            AI_RUNTIME_SECTION
        )

        if not isinstance(section, Mapping):
            return cls.disabled()

        enabled = _bool_value(
            section.get("enabled"),
            default=False,
        )

        provider = (
            _text_value(
                section.get("provider")
            )
            or "openai"
        ).casefold()

        model = _text_value(
            section.get("model")
        )

        if not enabled:
            return cls(
                enabled=False,
                provider=provider,
                model=model,
            )

        if provider not in SUPPORTED_PROVIDERS:
            return cls(
                enabled=False,
                provider=provider,
                model=model,
            )

        return cls(
            enabled=True,
            provider=provider,
            model=model,
        )

    def to_document_runtime_config(
        self,
    ) -> DocumentIntelligenceRuntimeConfig:
        return DocumentIntelligenceRuntimeConfig(
            ai_enabled=self.enabled,
            provider=self.provider,
            model=self.model,
        )


def resolve_document_runtime_config_from_admin_payload(
    payload: Mapping[str, Any] | None,
) -> DocumentIntelligenceRuntimeConfig:
    """Convert ADMIN configuration payload into document AI runtime config.

    Safety policy:
    - Missing AI section means AI disabled.
    - Invalid provider means AI disabled.
    - API keys are never accepted from the payload.
    - Model may be omitted so the provider can use its own safe default.
    """

    return (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(payload)
        .to_document_runtime_config()
    )
