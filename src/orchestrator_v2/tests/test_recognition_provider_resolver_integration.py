from src.orchestrator_v2.recognition.recognition_provider_registry import (
    RecognitionProviderRegistry,
)
from src.orchestrator_v2.recognition.recognition_provider_resolver import (
    RecognitionProviderResolver,
)


class DemoProvider:
    """
    Minimal provider used only for integration testing.

    Must satisfy the frozen RecognitionProviderRegistry contract.
    """

    def __init__(self, provider_id):
        self.provider_id = provider_id


def _expect_exception(action):
    try:
        action()
    except Exception:
        return True

    return False


def main():
    print("=" * 72)
    print("V2-ORCH-005D.4 - RESOLVER <-> REAL REGISTRY INTEGRATION TEST")
    print("=" * 72)

    # ---------------------------------------------------------
    # Setup
    # ---------------------------------------------------------

    registry = RecognitionProviderRegistry()

    provider = DemoProvider("demo-provider")

    # ---------------------------------------------------------
    # I1 - Provider registration
    # ---------------------------------------------------------

    registry.register(provider)

    passed_i1 = registry.get("demo-provider") is provider

    print(
        f"I1 Provider registered in real registry: "
        f"{'PASS' if passed_i1 else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I2 - Resolver -> Registry
    # ---------------------------------------------------------

    resolver = RecognitionProviderResolver(registry)

    resolved = resolver.resolve("demo-provider")

    passed_i2 = resolved is provider

    print(
        f"I2 Resolver resolves through real registry: "
        f"{'PASS' if passed_i2 else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I3 - Provider ID normalization
    # ---------------------------------------------------------

    resolved_normalized = resolver.resolve(
        "  demo-provider  "
    )

    passed_i3 = resolved_normalized is provider

    print(
        f"I3 Normalized lookup through real registry: "
        f"{'PASS' if passed_i3 else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I4 - Unknown provider must remain blocked
    # ---------------------------------------------------------

    passed_i4 = _expect_exception(
        lambda: resolver.resolve(
            "unknown-provider"
        )
    )

    print(
        f"I4 Unknown provider blocked through registry: "
        f"{'PASS' if passed_i4 else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # I5 - Provider identity must not change
    # ---------------------------------------------------------

    resolved_again = resolver.resolve(
        "demo-provider"
    )

    passed_i5 = resolved_again is provider

    print(
        f"I5 Provider identity preserved: "
        f"{'PASS' if passed_i5 else 'FAIL'}"
    )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    results = [
        passed_i1,
        passed_i2,
        passed_i3,
        passed_i4,
        passed_i5,
    ]

    print()

    if all(results):
        print(
            "RESULT: PASS - RESOLVER / REAL REGISTRY "
            "INTEGRATION VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - RESOLVER / REAL REGISTRY "
            "INTEGRATION VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()