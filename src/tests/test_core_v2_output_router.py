from typing import Any

from src.core_v2.routing import (
    OutputAdapter,
    OutputRouter,
)


class FakeBase44Adapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-BASE44"

    @property
    def output_type(self) -> str:
        return "BASE44"

    def render(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        return {
            "adapter": self.adapter_id,
            "output_type": self.output_type,
            "data": data,
            "context": context or {},
        }


class FakePdfAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-PDF"

    @property
    def output_type(self) -> str:
        return "PDF"

    def render(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        return {
            "adapter": self.adapter_id,
            "output_type": self.output_type,
            "data": data,
            "context": context or {},
        }


def main():

    print("=" * 72)
    print(
        "V2-CORE-008 - "
        "OUTPUT ROUTER TEST"
    )
    print("=" * 72)

    router = OutputRouter()

    base44 = FakeBase44Adapter()
    pdf = FakePdfAdapter()

    router.register(base44)
    router.register(pdf)

    assert len(
        router.all()
    ) == 2

    print(
        "Register adapters: PASS"
    )

    resolved_base44 = (
        router.resolve(
            "BASE44"
        )
    )

    assert (
        resolved_base44
        is base44
    )

    print(
        "Resolve BASE44: PASS"
    )

    resolved_pdf = (
        router.resolve(
            "PDF"
        )
    )

    assert (
        resolved_pdf
        is pdf
    )

    print(
        "Resolve PDF: PASS"
    )

    source_data = {
        "academic_unit_id": "AU-001",
        "name": "Toán",
    }

    result = (
        resolved_base44.render(
            source_data,
            context={
                "mode": "VIEW",
            },
        )
    )

    assert (
        result["data"]
        is source_data
    )

    assert (
        result["output_type"]
        == "BASE44"
    )

    print(
        "Render output: PASS"
    )

    duplicate_blocked = False

    try:
        router.register(
            FakeBase44Adapter()
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate adapter blocked: PASS"
    )

    unknown_blocked = False

    try:
        router.resolve(
            "UNKNOWN_OUTPUT"
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print(
        "Unknown output blocked: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - OUTPUT ROUTER VERIFIED"
    )


if __name__ == "__main__":
    main()