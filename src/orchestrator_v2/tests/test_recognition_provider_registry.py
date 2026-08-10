from typing import Any

from src.orchestrator_v2.contracts import (
    RecognitionEvidence,
)

from src.orchestrator_v2.recognition import (
    RecognitionProvider,
    RecognitionProviderRegistry,
)


class FakeRegistryProvider(
    RecognitionProvider
):

    @property
    def provider_id(self) -> str:
        return "REGISTRY_PROVIDER"

    def recognize(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[RecognitionEvidence, ...]:

        return (
            RecognitionEvidence(
                provider_id=self.provider_id,
                candidate_data_type_id="COMPETENCY",
                confidence=0.98,
                authority=1.0,
                evidence="Registry match.",
            ),
        )


class FakeRuleProvider(
    RecognitionProvider
):

    @property
    def provider_id(self) -> str:
        return "RULE_PROVIDER"

    def recognize(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[RecognitionEvidence, ...]:

        return (
            RecognitionEvidence(
                provider_id=self.provider_id,
                candidate_data_type_id="COMPETENCY",
                confidence=0.90,
                authority=0.80,
                evidence="Rule match.",
            ),
        )


def main():

    print("=" * 72)
    print(
        "V2-ORCH-005C - "
        "RECOGNITION PROVIDER REGISTRY TEST"
    )
    print("=" * 72)

    registry = RecognitionProviderRegistry()

    provider_1 = FakeRegistryProvider()
    provider_2 = FakeRuleProvider()

    registry.register(
        provider_1
    )

    registry.register(
        provider_2
    )

    assert len(
        registry.all()
    ) == 2

    print(
        "Register providers: PASS"
    )

    assert registry.exists(
        "REGISTRY_PROVIDER"
    )

    assert registry.exists(
        "RULE_PROVIDER"
    )

    print(
        "Provider exists lookup: PASS"
    )

    resolved = registry.get(
        "REGISTRY_PROVIDER"
    )

    assert (
        resolved
        is provider_1
    )

    print(
        "Resolve correct provider: PASS"
    )

    evidence = resolved.recognize(
        "năng lực tư duy toán học"
    )

    assert len(evidence) == 1

    assert (
        evidence[0].candidate_data_type_id
        == "COMPETENCY"
    )

    print(
        "Provider execution through registry: PASS"
    )

    duplicate_blocked = False

    try:
        registry.register(
            FakeRegistryProvider()
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate provider blocked: PASS"
    )

    unknown_blocked = False

    try:
        registry.get(
            "UNKNOWN_PROVIDER"
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print(
        "Unknown provider blocked: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - RECOGNITION PROVIDER REGISTRY VERIFIED"
    )


if __name__ == "__main__":
    main()