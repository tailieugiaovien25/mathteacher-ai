from src.orchestrator_v2.recognition.recognition_execution_service import (
    RecognitionExecutionService,
)


class FakeProvider:
    def __init__(self):
        self.received_data = None
        self.received_context = None
        self.result = ("evidence-1", "evidence-2")

    def recognize(self, data, *, context=None):
        self.received_data = data
        self.received_context = context
        return self.result


class FakeResolver:
    def __init__(self):
        self.provider = FakeProvider()
        self.requested_provider_id = None

    def resolve(self, provider_id):
        self.requested_provider_id = provider_id
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
    print("=" * 72)
    print("V2-ORCH-005E.3 - RECOGNITION EXECUTION SERVICE CONTRACT TEST")
    print("=" * 72)

    results = []

    # E1 - resolver is mandatory
    passed = _expect_exception(
        ValueError,
        lambda: RecognitionExecutionService(None),
    )

    results.append(passed)

    print(
        f"E1 Missing resolver blocked: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # E2 - provider resolution delegated to resolver
    resolver = FakeResolver()
    service = RecognitionExecutionService(resolver)

    service.execute(
        "provider-a",
        {"value": 123},
    )

    passed = (
        resolver.requested_provider_id
        == "provider-a"
    )

    results.append(passed)

    print(
        f"E2 Provider resolution delegated: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # E3 - input data forwarded unchanged
    resolver = FakeResolver()
    service = RecognitionExecutionService(resolver)

    data = {
        "value": 123,
        "items": [1, 2, 3],
    }

    service.execute(
        "provider-a",
        data,
    )

    passed = (
        resolver.provider.received_data
        is data
    )

    results.append(passed)

    print(
        f"E3 Input identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # E4 - context forwarded unchanged
    resolver = FakeResolver()
    service = RecognitionExecutionService(resolver)

    context = {
        "source": "contract-test",
    }

    service.execute(
        "provider-a",
        {"value": 123},
        context=context,
    )

    passed = (
        resolver.provider.received_context
        is context
    )

    results.append(passed)

    print(
        f"E4 Context identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # E5 - None context forwarded correctly
    resolver = FakeResolver()
    service = RecognitionExecutionService(resolver)

    service.execute(
        "provider-a",
        {"value": 123},
    )

    passed = (
        resolver.provider.received_context
        is None
    )

    results.append(passed)

    print(
        f"E5 None context preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # E6 - provider result returned unchanged
    resolver = FakeResolver()
    service = RecognitionExecutionService(resolver)

    result = service.execute(
        "provider-a",
        {"value": 123},
    )

    passed = (
        result
        is resolver.provider.result
    )

    results.append(passed)

    print(
        f"E6 Provider result identity preserved: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    # E7 - provider exception must propagate
    class FailingProvider:
        def recognize(self, data, *, context=None):
            raise RuntimeError(
                "provider failure"
            )

    class FailingResolver:
        def resolve(self, provider_id):
            return FailingProvider()

    service = RecognitionExecutionService(
        FailingResolver()
    )

    passed = _expect_exception(
        RuntimeError,
        lambda: service.execute(
            "provider-a",
            {"value": 123},
        ),
    )

    results.append(passed)

    print(
        f"E7 Provider exception propagated: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print()

    if all(results):
        print(
            "RESULT: PASS - RECOGNITION EXECUTION "
            "SERVICE CONTRACT VERIFIED"
        )
    else:
        print(
            "RESULT: FAIL - RECOGNITION EXECUTION "
            "SERVICE CONTRACT VIOLATED"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()