from __future__ import annotations

from document_intelligence.admin_ai_runtime_config import (
    AI_RUNTIME_SECTION,
    AdminAIRuntimeConfiguration,
    SUPPORTED_PROVIDERS,
    resolve_document_runtime_config_from_admin_payload,
)
from document_intelligence.runtime_config import (
    DocumentIntelligenceRuntimeConfig,
)


def test_missing_payload_disables_ai() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(None)
    )

    assert resolved.enabled is False
    assert resolved.provider == "openai"
    assert resolved.model is None


def test_missing_ai_section_disables_ai() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                "template_profile": {
                    "profile_name": "example",
                }
            }
        )
    )

    assert resolved.enabled is False


def test_empty_ai_section_disables_ai() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {},
            }
        )
    )

    assert resolved.enabled is False
    assert resolved.provider == "openai"


def test_gemini_configuration_is_accepted() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "gemini",
                    "model": "gemini-3.5-flash-lite",
                }
            }
        )
    )

    assert resolved.enabled is True
    assert resolved.provider == "gemini"
    assert resolved.model == "gemini-3.5-flash-lite"


def test_openai_configuration_is_accepted() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "openai",
                    "model": "gpt-test",
                }
            }
        )
    )

    assert resolved.enabled is True
    assert resolved.provider == "openai"
    assert resolved.model == "gpt-test"


def test_provider_is_normalized() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "  GeMiNi  ",
                }
            }
        )
    )

    assert resolved.enabled is True
    assert resolved.provider == "gemini"


def test_unknown_provider_disables_ai() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "future-provider",
                    "model": "future-model",
                }
            }
        )
    )

    assert resolved.enabled is False
    assert resolved.provider == "future-provider"
    assert resolved.model == "future-model"


def test_model_may_be_blank() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "gemini",
                    "model": "   ",
                }
            }
        )
    )

    assert resolved.enabled is True
    assert resolved.model is None


def test_string_true_is_accepted() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": "true",
                    "provider": "gemini",
                }
            }
        )
    )

    assert resolved.enabled is True


def test_string_false_disables_ai() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": "false",
                    "provider": "gemini",
                }
            }
        )
    )

    assert resolved.enabled is False


def test_non_mapping_ai_section_disables_ai() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: "gemini",
            }
        )
    )

    assert resolved.enabled is False


def test_api_key_field_is_ignored() -> None:
    resolved = (
        AdminAIRuntimeConfiguration
        .from_configuration_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "gemini",
                    "model": "gemini-test",
                    "api_key": "must-not-be-used",
                    "secret": "must-not-be-used",
                    "token": "must-not-be-used",
                }
            }
        )
    )

    assert resolved.enabled is True
    assert resolved.provider == "gemini"
    assert resolved.model == "gemini-test"
    assert not hasattr(
        resolved,
        "api_key",
    )
    assert not hasattr(
        resolved,
        "secret",
    )
    assert not hasattr(
        resolved,
        "token",
    )


def test_supported_providers_are_current_registry_baseline() -> None:
    assert SUPPORTED_PROVIDERS == frozenset(
        {
            "gemini",
            "openai",
        }
    )


def test_conversion_returns_existing_runtime_config_type() -> None:
    resolved = (
        resolve_document_runtime_config_from_admin_payload(
            {
                AI_RUNTIME_SECTION: {
                    "enabled": True,
                    "provider": "gemini",
                    "model": "gemini-test",
                }
            }
        )
    )

    assert isinstance(
        resolved,
        DocumentIntelligenceRuntimeConfig,
    )
    assert resolved.ai_enabled is True
    assert resolved.provider == "gemini"
    assert resolved.model == "gemini-test"


def test_missing_ai_section_does_not_inherit_environment() -> None:
    resolved = (
        resolve_document_runtime_config_from_admin_payload(
            {
                "template_profile": {},
            }
        )
    )

    assert resolved == DocumentIntelligenceRuntimeConfig(
        ai_enabled=False,
        provider="openai",
        model=None,
    )


def test_input_payload_is_not_mutated() -> None:
    payload = {
        AI_RUNTIME_SECTION: {
            "enabled": True,
            "provider": "gemini",
            "model": "gemini-test",
        },
        "template_profile": {
            "profile_name": "original",
        },
    }

    original = {
        AI_RUNTIME_SECTION: dict(
            payload[AI_RUNTIME_SECTION]
        ),
        "template_profile": dict(
            payload["template_profile"]
        ),
    }

    resolve_document_runtime_config_from_admin_payload(
        payload
    )

    assert payload == original
