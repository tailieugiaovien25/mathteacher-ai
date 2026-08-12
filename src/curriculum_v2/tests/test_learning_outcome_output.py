from typing import Any

from src.core_v2.routing import (
    OutputAdapter,
    OutputRouter,
)

from src.curriculum_v2.models import (
    LearningOutcome,
)


class Base44LearningOutcomeAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-LO-BASE44"

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
            "id": data.learning_outcome_id,
            "code": data.code,
            "statement": data.statement,
            "context": context or {},
        }


class DocumentLearningOutcomeAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-LO-DOCUMENT"

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
            "reference": data.code,
            "content": data.statement,
            "context": context or {},
        }


def main():

    print("=" * 72)
    print(
        "V2-MODULE-002F - "
        "LEARNING OUTCOME T6 OUTPUT TEST"
    )
    print("=" * 72)

    outcome = LearningOutcome(
        learning_outcome_id="LO-001",
        curriculum_ref="CURR-001",
        code="LO-001",
        statement=(
            "Thực hiện được một yêu cầu "
            "học tập xác định."
        ),
        outcome_type="GENERAL",
        status="ACTIVE",
    )

    router = OutputRouter()

    base44_adapter = (
        Base44LearningOutcomeAdapter()
    )

    document_adapter = (
        DocumentLearningOutcomeAdapter()
    )

    router.register(
        base44_adapter
    )

    router.register(
        document_adapter
    )

    # --------------------------------------------------------
    # 1. BASE44 output
    # --------------------------------------------------------

    base44_output = (
        router.resolve(
            "BASE44"
        ).render(
            outcome,
            context={
                "mode": "VIEW",
            },
        )
    )

    assert (
        base44_output["id"]
        == "LO-001"
    )

    assert (
        base44_output["statement"]
        == outcome.statement
    )

    print(
        "BASE44 output: PASS"
    )

    # --------------------------------------------------------
    # 2. Document output
    # --------------------------------------------------------

    document_output = (
        router.resolve(
            "DOCUMENT"
        ).render(
            outcome,
            context={
                "product": "LESSON_PLAN",
            },
        )
    )

    assert (
        document_output["reference"]
        == "LO-001"
    )

    assert (
        document_output["content"]
        == outcome.statement
    )

    print(
        "Document output: PASS"
    )

    # --------------------------------------------------------
    # 3. Source data unchanged
    # --------------------------------------------------------

    assert (
        outcome.learning_outcome_id
        == "LO-001"
    )

    assert (
        outcome.statement
        == (
            "Thực hiện được một yêu cầu "
            "học tập xác định."
        )
    )

    print(
        "Source YCCD unchanged: PASS"
    )

    # --------------------------------------------------------
    # 4. New output type
    # --------------------------------------------------------

    class FutureLearningOutcomeAdapter(
        OutputAdapter
    ):

        @property
        def adapter_id(self) -> str:
            return "OUT-LO-FUTURE"

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
                "value": data.statement,
                "context": context or {},
            }

    future_adapter = (
        FutureLearningOutcomeAdapter()
    )

    router.register(
        future_adapter
    )

    future_output = (
        router.resolve(
            "FUTURE_OUTPUT"
        ).render(
            outcome
        )
    )

    assert (
        future_output["value"]
        == outcome.statement
    )

    print(
        "New output without model/core change: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - T6 OUTPUT VERIFIED"
    )


if __name__ == "__main__":
    main()