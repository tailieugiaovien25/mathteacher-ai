from __future__ import annotations

import pytest

from document_intelligence.provider_contract import (
    AIProviderDescriptor,
)
from document_intelligence.provider_registry import (
    AIProviderRegistry,
    build_default_ai_provider_registry,
)


def test_descriptor_rejects_blank_provider_id() -> None:
    with pytest.raises(ValueError):
        AIProviderDescriptor(
            provider_id="",
            display_name="Test",
        )


def test_descriptor_rejects_non_normalized_id() -> None:
    with pytest.raises(ValueError):
        AIProviderDescriptor(
            provider_id="Gemini",
            display_name="Gemini",
        )


def test_registry_register_and_lookup() -> None:
    registry = AIProviderRegistry()

    descriptor = AIProviderDescriptor(
        provider_id="test",
        display_name="Test Provider",
    )

    registry.register(descriptor)

    assert registry.get("test") == descriptor
    assert registry.get(" TEST ") == descriptor


def test_registry_rejects_duplicate_provider() -> None:
    registry = AIProviderRegistry()

    descriptor = AIProviderDescriptor(
        provider_id="test",
        display_name="Test",
    )

    registry.register(descriptor)

    with pytest.raises(ValueError):
        registry.register(descriptor)


def test_require_rejects_unknown_provider() -> None:
    registry = AIProviderRegistry()

    with pytest.raises(KeyError):
        registry.require("missing")


def test_default_registry_contains_gemini_and_openai() -> None:
    registry = build_default_ai_provider_registry()

    ids = {
        item.provider_id
        for item in registry.list_all()
    }

    assert ids == {
        "gemini",
        "openai",
    }


def test_document_intelligence_capability_lists_both() -> None:
    registry = build_default_ai_provider_registry()

    ids = {
        item.provider_id
        for item in registry.list_document_intelligence()
    }

    assert ids == {
        "gemini",
        "openai",
    }


def test_lesson_authoring_capability_lists_both() -> None:
    registry = build_default_ai_provider_registry()

    ids = {
        item.provider_id
        for item in registry.list_lesson_authoring()
    }

    assert ids == {
        "gemini",
        "openai",
    }


def test_descriptor_contains_no_secret_fields() -> None:
    descriptor = AIProviderDescriptor(
        provider_id="test",
        display_name="Test",
    )

    assert not hasattr(descriptor, "api_key")
    assert not hasattr(descriptor, "secret")
    assert not hasattr(descriptor, "token")


def test_registry_stores_metadata_only() -> None:
    registry = build_default_ai_provider_registry()

    for descriptor in registry.list_all():
        assert isinstance(
            descriptor,
            AIProviderDescriptor,
        )
