from __future__ import annotations

from collections.abc import Iterable

from document_intelligence.provider_contract import (
    AIProviderDescriptor,
)


class AIProviderRegistry:
    """In-memory provider metadata registry.

    This registry stores no API keys and performs no network calls.
    Runtime provider construction remains outside this class.
    """

    def __init__(
        self,
        descriptors: Iterable[AIProviderDescriptor] | None = None,
    ) -> None:
        self._items: dict[str, AIProviderDescriptor] = {}

        for descriptor in descriptors or ():
            self.register(descriptor)

    def register(
        self,
        descriptor: AIProviderDescriptor,
    ) -> None:
        provider_id = descriptor.provider_id

        if provider_id in self._items:
            raise ValueError(
                f"AI provider already registered: {provider_id}"
            )

        self._items[provider_id] = descriptor

    def get(
        self,
        provider_id: str,
    ) -> AIProviderDescriptor | None:
        return self._items.get(provider_id.strip().lower())

    def require(
        self,
        provider_id: str,
    ) -> AIProviderDescriptor:
        descriptor = self.get(provider_id)

        if descriptor is None:
            raise KeyError(
                f"Unknown AI provider: {provider_id}"
            )

        return descriptor

    def list_all(self) -> tuple[AIProviderDescriptor, ...]:
        return tuple(
            self._items[key]
            for key in sorted(self._items)
        )

    def list_document_intelligence(
        self,
    ) -> tuple[AIProviderDescriptor, ...]:
        return tuple(
            item
            for item in self.list_all()
            if item.supports_document_intelligence
        )

    def list_lesson_authoring(
        self,
    ) -> tuple[AIProviderDescriptor, ...]:
        return tuple(
            item
            for item in self.list_all()
            if item.supports_lesson_authoring
        )


def build_default_ai_provider_registry() -> AIProviderRegistry:
    """Return provider metadata only.

    No provider is instantiated here and no credential is read.
    """

    return AIProviderRegistry(
        [
            AIProviderDescriptor(
                provider_id="gemini",
                display_name="Google Gemini",
                supports_document_intelligence=True,
                supports_lesson_authoring=True,
            ),
            AIProviderDescriptor(
                provider_id="openai",
                display_name="OpenAI",
                supports_document_intelligence=True,
                supports_lesson_authoring=True,
            ),
        ]
    )
