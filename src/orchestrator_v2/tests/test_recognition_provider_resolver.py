from src.orchestrator_v2.recognition.recognition_provider_resolver import (
    RecognitionProviderResolver,
)


class FakeProvider:
    pass


class FakeRegistry:
    def __init__(self):
        self.provider = FakeProvider()
        self.requested_name = None

    def get(self, provider_name):
        self.requested_name = provider_name
        return self.provider


def _expect_exception(exception_type, action):
    try:
        action()
    except exception_type:
        return True
    except Exception:
        return False

    return False


def main():
    print("=" * 68)
    print("V2-ORCH-005D - RECOGNITION PROVIDER RESOLVER CONTRACT TEST")
    print("=" * 68)

    results = []

    # D1 - registry is mandatory
    passed = _expect_exception(
        ValueError,
        lambda: RecognitionProviderResolver(None),
    )
    results.append(passed)
    print(f"D1 Missing registry blocked: {'PASS' if passed else 'FAIL'}")

    # D2 - provider name must be string
    registry = FakeRegistry()
    resolver = RecognitionProviderResolver(registry)

    passed = _expect_exception(
        TypeError,
        lambda: resolver.resolve(None),
    )
    results.append(passed)
    print(f"D2 Non-string provider name blocked: {'PASS' if passed else 'FAIL'}")

    # D3 - empty provider name blocked
    passed = _expect_exception(
        ValueError,
        lambda: resolver.resolve(""),
    )
    results.append(passed)
    print(f"D3 Empty provider name blocked: {'PASS' if passed else 'FAIL'}")

    # D4 - whitespace-only provider name blocked
    passed = _expect_exception(
        ValueError,
        lambda: resolver.resolve("   "),
    )
    results.append(passed)
    print(f"D4 Whitespace provider name blocked: {'PASS' if passed else 'FAIL'}")

    # D5 - provider name normalized before registry lookup
    registry = FakeRegistry()
    resolver = RecognitionProviderResolver(registry)

    resolver.resolve("  demo-provider  ")

    passed = registry.requested_name == "demo-provider"
    results.append(passed)
    print(f"D5 Provider name normalized: {'PASS' if passed else 'FAIL'}")

    # D6 - resolver delegates lookup to registry
    registry = FakeRegistry()
    resolver = RecognitionProviderResolver(registry)

    resolver.resolve("provider-a")

    passed = registry.requested_name == "provider-a"
    results.append(passed)
    print(f"D6 Registry lookup delegated: {'PASS' if passed else 'FAIL'}")

    # D7 - exact provider object returned
    registry = FakeRegistry()
    resolver = RecognitionProviderResolver(registry)

    resolved = resolver.resolve("provider-a")

    passed = resolved is registry.provider
    results.append(passed)
    print(f"D7 Exact provider returned: {'PASS' if passed else 'FAIL'}")

    print()

    if all(results):
        print("RESULT: PASS - RECOGNITION PROVIDER RESOLVER CONTRACT VERIFIED")
    else:
        print("RESULT: FAIL - RECOGNITION PROVIDER RESOLVER CONTRACT VIOLATED")
        raise SystemExit(1)


if __name__ == "__main__":
    main()