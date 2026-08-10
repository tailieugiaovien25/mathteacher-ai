from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)
from src.orchestrator_v2.recognition.recognition_execution_service import (
    RecognitionExecutionService,
)
from src.orchestrator_v2.recognition.recognition_provider import (
    RecognitionProvider,
)
from src.orchestrator_v2.recognition.recognition_provider_registry import (
    RecognitionProviderRegistry,
)
from src.orchestrator_v2.recognition.recognition_provider_resolver import (
    RecognitionProviderResolver,
)


class DemoRecognitionProvider(RecognitionProvider):
    """
    Minimal real RecognitionProvider implementation
    for V2-ORCH-005E.4 integration testing.
    """

    @property
    def provider_id(self) -> str:
        return "demo-provider"

    def recognize(
        self,
        data,
        *,
        context=None,
    ) -> tuple[RecognitionEvidence, ...]:
        return (
            RecognitionEvidence(
                provider_id=self.provider_id,
                candidate_data_type_id="demo-data-type",
                confidence=0.95,
                authority=1.0,
                evidence="demo recognition evidence",
                metadata={
                    "input_identity": id(data),
                    "context_identity": (
                        id(context)
                        if context is not None
                        else None
                    ),
                },
            ),
        )


def _expect_exception(exception_type, action):
    try:
        action()
    except exception_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 76)
    print(
        "V2-ORCH-005E.4 - RECOGNITION EXECUTION "
        "SERVICE INTEGRATION TEST"
    )
    print("=" * 76)

    results = []

    # ---------------------------------------------------------
    # Real architecture chain
    # ---------------------------------------------------------

    registry = RecognitionProviderRegistry()

    provider = DemoRecognitionProvider()

    registry.register(provider)

    resolver = RecognitionProviderResolver(
        registry
    )

    service = RecognitionExecutionService(
        resolver
    )

    # ---------------------------------------------------------
    # I1 - Real provider registered
    # ---------------------------------------------------------

    passed = (
        registry.get("demo-provider")
        is provider
    )

    results.append(passed)

    print(
        f"I1 Real provider registered: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I2 - Full chain executes
    # ---------------------------------------------------------

    data = {
        "value": 123,
    }

    context = {
        "source": "integration-test",
    }

    evidence = service.execute(
        "demo-provider",
        data,
        context=context,
    )

    passed = (
        isinstance(evidence, tuple)
        and len(evidence) == 1
        and isinstance(
            evidence[0],
            RecognitionEvidence,
        )
    )

    results.append(passed)

    print(
        f"I2 Full recognition chain executes: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I3 - Evidence provider identity correct
    # ---------------------------------------------------------

    passed = (
        evidence[0].provider_id
        == "demo-provider"
    )

    results.append(passed)

    print(
        f"I3 Evidence provider_id preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I4 - Evidence candidate type preserved
    # ---------------------------------------------------------

    passed = (
        evidence[0].candidate_data_type_id
        == "demo-data-type"
    )

    results.append(passed)

    print(
        f"I4 Candidate data type preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I5 - Input and context reach provider unchanged
    # ---------------------------------------------------------

    passed = (
        evidence[0].metadata[
            "input_identity"
        ]
        == id(data)
        and evidence[0].metadata[
            "context_identity"
        ]
        == id(context)
    )

    results.append(passed)

    print(
        f"I5 Input/context identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I6 - Resolver normalization works in full chain
    # ---------------------------------------------------------

    normalized_result = service.execute(
        "  demo-provider  ",
        data,
        context=context,
    )

    passed = (
        len(normalized_result) == 1
        and normalized_result[0].provider_id
        == "demo-provider"
    )

    results.append(passed)

    print(
        f"I6 Provider ID normalization preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I7 - Unknown provider remains blocked
    # ---------------------------------------------------------

    passed = _expect_exception(
        KeyError,
        lambda: service.execute(
            "unknown-provider",
            data,
            context=context,
        ),
    )

    results.append(passed)

    print(
        f"I7 Unknown provider blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    print()

    if all(results):
        print(
            "RESULT: PASS - RECOGNITION EXECUTION "
            "SERVICE INTEGRATION VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - RECOGNITION EXECUTION "
            "SERVICE INTEGRATION VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()