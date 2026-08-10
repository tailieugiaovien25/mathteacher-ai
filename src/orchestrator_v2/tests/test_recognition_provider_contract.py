from typing import Any

from src.orchestrator_v2.contracts import (
    RecognitionEvidence,
)

from src.orchestrator_v2.recognition import (
    RecognitionProvider,
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


def main():

    print("=" * 72)
    print(
        "V2-ORCH-005B - "
        "RECOGNITION PROVIDER CONTRACT TEST"
    )
    print("=" * 72)

    provider = FakeRegistryProvider()

    assert (
        provider.provider_id
        == "REGISTRY_PROVIDER"
    )

    print(
        "Provider identity: PASS"
    )

    evidence = provider.recognize(
        "năng lực tư duy toán học"
    )

    assert len(evidence) == 1

    item = evidence[0]

    assert (
        item.candidate_data_type_id
        == "COMPETENCY"
    )

    assert item.confidence == 0.98
    assert item.authority == 1.0

    print(
        "RecognitionEvidence returned: PASS"
    )

    # Provider chỉ trả Evidence,
    # không trả RecognitionResult.
    assert isinstance(
        item,
        RecognitionEvidence,
    )

    print(
        "Provider returns evidence only: PASS"
    )

    # Evidence không chứa Identity cuối cùng.
    fields = set(
        item.__dataclass_fields__
    )

    assert "resolved_id" not in fields
    assert "processor_id" not in fields

    print(
        "No identity / processor leakage: PASS"
    )

    # Confidence và authority độc lập.
    assert (
        item.confidence
        != item.authority
    )

    print(
        "Confidence != Authority: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - RECOGNITION PROVIDER CONTRACT VERIFIED"
    )


if __name__ == "__main__":
    main()