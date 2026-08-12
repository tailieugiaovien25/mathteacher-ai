from typing import runtime_checkable

from src.multiai_v2.contracts import (
    CapabilityRequest,
    ExecutionResult,
    ProviderCapability,
)
from src.multiai_v2.provider import AIProvider


def test_ai_provider_is_runtime_checkable_protocol():
    assert getattr(AIProvider, "_is_protocol", False) is True
    assert getattr(AIProvider, "_is_runtime_protocol", False) is True


def test_structural_provider_satisfies_protocol():
    class FakeProvider:
        @property
        def provider_id(self) -> str:
            return "provider-a"

        def capabilities(self) -> tuple[ProviderCapability, ...]:
            return (
                ProviderCapability(
                    capability_id="lesson.pedagogical_proposal",
                    version="1.0",
                ),
            )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> ExecutionResult:
            return ExecutionResult(
                capability_id=request.capability_id,
                capability_version=request.capability_version,
                provider_id=self.provider_id,
                output_data={"value": "generated"},
                success=True,
            )

    provider = FakeProvider()

    assert isinstance(provider, AIProvider)


def test_provider_can_execute_capability_request():
    class FakeProvider:
        @property
        def provider_id(self) -> str:
            return "provider-a"

        def capabilities(self) -> tuple[ProviderCapability, ...]:
            return (
                ProviderCapability(
                    capability_id="lesson.pedagogical_proposal",
                    version="1.0",
                ),
            )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> ExecutionResult:
            return ExecutionResult(
                capability_id=request.capability_id,
                capability_version=request.capability_version,
                provider_id=self.provider_id,
                output_data={"value": "generated"},
                success=True,
            )

    provider = FakeProvider()

    request = CapabilityRequest(
        capability_id="lesson.pedagogical_proposal",
        capability_version="1.0",
        input_data={"lesson": "fractions"},
    )

    result = provider.execute(request)

    assert isinstance(result, ExecutionResult)
    assert result.capability_id == request.capability_id
    assert result.capability_version == request.capability_version
    assert result.provider_id == "provider-a"
    assert result.success is True


def test_provider_exposes_capabilities():
    class FakeProvider:
        @property
        def provider_id(self) -> str:
            return "provider-a"

        def capabilities(self) -> tuple[ProviderCapability, ...]:
            return (
                ProviderCapability(
                    capability_id="lesson.pedagogical_proposal",
                    version="1.0",
                ),
            )

        def execute(
            self,
            request: CapabilityRequest,
        ) -> ExecutionResult:
            raise NotImplementedError

    provider = FakeProvider()

    capabilities = provider.capabilities()

    assert capabilities == (
        ProviderCapability(
            capability_id="lesson.pedagogical_proposal",
            version="1.0",
        ),
    )


def test_provider_interface_has_no_routing_or_acceptance_responsibility():
    forbidden = {
        "route",
        "select_provider",
        "fallback",
        "accept",
        "reject",
        "validate",
        "rank",
    }

    assert forbidden.isdisjoint(AIProvider.__dict__)