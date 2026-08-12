from typing import Any

from src.core_v2.routing import (
    OutputAdapter,
    OutputRouter,
)

from src.curriculum_v2.models import (
    CurriculumNode,
)


class Base44CurriculumAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-CN-BASE44"

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
            "id": data.curriculum_node_id,
            "code": data.code,
            "name": data.name,
            "node_type": data.node_type,
            "context": context or {},
        }


class DocumentCurriculumAdapter(
    OutputAdapter
):

    @property
    def adapter_id(self) -> str:
        return "OUT-CN-DOCUMENT"

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
            "reference": data.code,
            "sequence": data.sequence,
            "context": context or {},
        }


def main():

    print("=" * 72)
    print(
        "V2-MODULE-001E-4 - "
        "CURRICULUM NODE T6 OUTPUT TEST"
    )
    print("=" * 72)

    node = CurriculumNode(
        curriculum_node_id="CN-001",
        curriculum_ref="CURR-001",
        code="BAI_001",
        name="Bài 1",
        node_type="LESSON",
        parent_id="CN-TOPIC-001",
        sequence=1,
    )

    router = OutputRouter()

    base44_adapter = (
        Base44CurriculumAdapter()
    )

    document_adapter = (
        DocumentCurriculumAdapter()
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
            node,
            context={
                "mode": "VIEW",
            },
        )
    )

    assert (
        base44_output["id"]
        == "CN-001"
    )

    assert (
        base44_output["name"]
        == "Bài 1"
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
            node,
            context={
                "template": "PPCT",
            },
        )
    )

    assert (
        document_output["title"]
        == "Bài 1"
    )

    assert (
        document_output["reference"]
        == "BAI_001"
    )

    print(
        "Document output: PASS"
    )

    # --------------------------------------------------------
    # 3. Source data unchanged
    # --------------------------------------------------------

    assert (
        node.curriculum_node_id
        == "CN-001"
    )

    assert node.code == "BAI_001"

    assert node.name == "Bài 1"

    assert node.node_type == "LESSON"

    assert (
        node.parent_id
        == "CN-TOPIC-001"
    )

    print(
        "Source data unchanged: PASS"
    )

    # --------------------------------------------------------
    # 4. New output type without changing model/core
    # --------------------------------------------------------

    class FutureOutputAdapter(
        OutputAdapter
    ):

        @property
        def adapter_id(self) -> str:
            return "OUT-CN-FUTURE"

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
        FutureOutputAdapter()
    )

    router.register(
        future_adapter
    )

    future_output = (
        router.resolve(
            "FUTURE_OUTPUT"
        ).render(
            node
        )
    )

    assert (
        future_output["value"]
        == "Bài 1"
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