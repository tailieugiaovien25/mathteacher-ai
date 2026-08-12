from typing import Any

from src.core_v2.routing import (
    OutputAdapter,
    OutputRouter,
)

from src.curriculum_v2.models import (
    Competency,
)


class Base44CompetencyAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-COMP-BASE44"

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
            "id": data.competency_id,
            "name": data.name,
            "type": data.competency_type,
            "context": context or {},
        }


class DocumentCompetencyAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-COMP-DOCUMENT"

    @property
    def output_type(self) -> str:
        return "DOCUMENT"

    def render(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:

        return {
            "title": data.name,
            "category": data.competency_type,
            "context": context or {},
        }


def main():

    print("=" * 72)
    print(
        "V2-MODULE-003G - "
        "COMPETENCY T6 OUTPUT TEST"
    )
    print("=" * 72)

    competency = Competency(
        competency_id="COMP-001",
        name="Tư duy và lập luận toán học",
        competency_type="SUBJECT_SPECIFIC",
        status="ACTIVE",
    )

    router = OutputRouter()

    base44_adapter = (
        Base44CompetencyAdapter()
    )

    document_adapter = (
        DocumentCompetencyAdapter()
    )

    router.register(
        base44_adapter
    )

    router.register(
        document_adapter
    )

    # 1. BASE44
    base44_output = (
        router.resolve(
            "BASE44"
        ).render(
            competency,
            context={
                "mode": "VIEW",
            },
        )
    )

    assert (
        base44_output["id"]
        == "COMP-001"
    )

    assert (
        base44_output["name"]
        == competency.name
    )

    print(
        "BASE44 output: PASS"
    )

    # 2. DOCUMENT
    document_output = (
        router.resolve(
            "DOCUMENT"
        ).render(
            competency,
            context={
                "product": "LESSON_PLAN",
            },
        )
    )

    assert (
        document_output["title"]
        == competency.name
    )

    assert (
        document_output["category"]
        == "SUBJECT_SPECIFIC"
    )

    print(
        "Document output: PASS"
    )

    # 3. Source unchanged
    assert (
        competency.competency_id
        == "COMP-001"
    )

    assert (
        competency.name
        == "Tư duy và lập luận toán học"
    )

    print(
        "Source competency unchanged: PASS"
    )

    # 4. New output type
    class FutureCompetencyAdapter(
        OutputAdapter
    ):

        @property
        def adapter_id(self) -> str:
            return "OUT-COMP-FUTURE"

        @property
        def output_type(self) -> str:
            return "FUTURE_OUTPUT"

        def render(
            self,
            data: Any,
            *,
            context: dict[str, Any] | None = None,
        ) -> Any:

            return {
                "value": data.name,
                "context": context or {},
            }

    future_adapter = (
        FutureCompetencyAdapter()
    )

    router.register(
        future_adapter
    )

    future_output = (
        router.resolve(
            "FUTURE_OUTPUT"
        ).render(
            competency
        )
    )

    assert (
        future_output["value"]
        == competency.name
    )

    print(
        "New output without model/core change: PASS"
    )

    # 5. P8 check
    assert (
        "official_code"
        not in base44_output
    )

    assert (
        "official_code"
        not in document_output
    )

    print(
        "P8 output independent from encoding: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - COMPETENCY T6 OUTPUT VERIFIED"
    )


if __name__ == "__main__":
    main()