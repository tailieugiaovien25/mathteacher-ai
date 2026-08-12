import pytest

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ExecutionResult,
    ProviderCapability,
)
from src.multiai_v2.provider import AIProvider
from src.multiai_v2.provider_registry import ProviderRegistry


class FakeProvider:
    def __init__(
        self,
        provider_id: str,
        capabilities: tuple[ProviderCapability, ...] = (),
    ) -> None:
        self._provider_id = provider_id
        self._capabilities = capabilities

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def capabilities(self) -> tuple[ProviderCapability, ...]:
        return self._capabilities

    def execute(
        self,
        request: CapabilityRequest,
    ) -> ExecutionResult:
        return ExecutionResult(
            capability_id=request.capability_id,
            capability_version=request.capability_version,
            provider_id=self.provider_id,
            output_data=None,
            success=True,
        )


def _provider(
    provider_id: str = "provider-a",
) -> FakeProvider:
    return FakeProvider(
        provider_id=provider_id,
        capabilities=(
            ProviderCapability(
                capability_id="lesson.pedagogical_proposal",
                version="1.0",
            ),
        ),
    )


def test_empty_registry_is_allowed():
    registry = ProviderRegistry()

    assert registry.providers() == ()


def test_provider_can_be_registered():
    registry = ProviderRegistry()
    provider = _provider()

    registry.register(provider)

    assert registry.providers() == (provider,)


def test_registered_provider_can_be_resolved():
    registry = ProviderRegistry()
    provider = _provider()

    registry.register(provider)

    assert registry.get("provider-a") is provider


def test_unknown_provider_returns_none():
    registry = ProviderRegistry()

    assert registry.get("provider-unknown") is None


def test_multiple_providers_can_be_registered():
    registry = ProviderRegistry()

    provider_a = _provider("provider-a")
    provider_b = _provider("provider-b")

    registry.register(provider_a)
    registry.register(provider_b)

    assert registry.providers() == (
        provider_a,
        provider_b,
    )


def test_duplicate_provider_id_is_blocked():
    registry = ProviderRegistry()

    registry.register(_provider("provider-a"))

    with pytest.raises(ValueError):
        registry.register(_provider("provider-a"))


def test_registration_requires_ai_provider():
    registry = ProviderRegistry()

    with pytest.raises(TypeError):
        registry.register(object())


def test_provider_id_is_normalized_for_registration():
    registry = ProviderRegistry()

    provider = _provider("  provider-a  ")

    registry.register(provider)

    assert registry.get("provider-a") is provider


def test_lookup_provider_id_is_normalized():
    registry = ProviderRegistry()
    provider = _provider("provider-a")

    registry.register(provider)

    assert registry.get("  provider-a  ") is provider


def test_empty_provider_id_is_blocked_on_registration():
    registry = ProviderRegistry()

    with pytest.raises(ValueError):
        registry.register(_provider("   "))


def test_empty_provider_id_is_blocked_on_lookup():
    registry = ProviderRegistry()

    with pytest.raises(ValueError):
        registry.get("   ")


def test_registered_object_satisfies_ai_provider_protocol():
    provider = _provider()

    assert isinstance(provider, AIProvider)


def test_registry_has_no_routing_or_execution_responsibility():
    forbidden = {
        "select_provider",
        "rank_provider",
        "route",
        "fallback",
        "execute",
        "accept",
        "reject",
    }

    assert forbidden.isdisjoint(ProviderRegistry.__dict__)