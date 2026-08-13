from typing import Any

from src.core_v2.processing import (
    Processor,
    ProcessorRouter,
)


class FakeAcademicUnitComposeProcessor(
    Processor
):

    @property
    def processor_id(self) -> str:
        return "PROC-AU-COMPOSE"

    @property
    def data_type_id(self) -> str:
        return "ACADEMIC_UNIT"

    @property
    def capability(self) -> str:
        return "COMPOSE"

    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        return {
            "processor": self.processor_id,
            "data": data,
            "context": context or {},
        }


def main():

    print("=" * 72)
    print(
        "V2-CORE-006 - "
        "PROCESSOR ROUTER TEST"
    )
    print("=" * 72)

    router = ProcessorRouter()

    processor = (
        FakeAcademicUnitComposeProcessor()
    )

    router.register(processor)

    assert router.exists(
        data_type_id="ACADEMIC_UNIT",
        capability="COMPOSE",
    )

    print(
        "Register processor: PASS"
    )

    resolved = router.resolve(
        data_type_id="ACADEMIC_UNIT",
        capability="COMPOSE",
    )

    assert resolved is processor

    print(
        "Resolve correct processor: PASS"
    )

    result = resolved.process(
        {
            "academic_unit_id": "AU-001",
            "name": "Toán",
        },
        context={
            "output": "LESSON_PLAN",
        },
    )

    assert (
        result["processor"]
        == "PROC-AU-COMPOSE"
    )

    assert (
        result["data"]["name"]
        == "Toán"
    )

    print(
        "Process data: PASS"
    )

    duplicate_blocked = False

    try:
        router.register(
            FakeAcademicUnitComposeProcessor()
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate route blocked: PASS"
    )

    unknown_blocked = False

    try:
        router.resolve(
            data_type_id="ACADEMIC_UNIT",
            capability="UNKNOWN",
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print(
        "Unknown route blocked: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - PROCESSOR ROUTER VERIFIED"
    )


if __name__ == "__main__":
    main()