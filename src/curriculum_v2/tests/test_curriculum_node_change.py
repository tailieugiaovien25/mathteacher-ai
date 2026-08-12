from dataclasses import replace

from src.curriculum_v2.models import (
    CurriculumNode,
)

from src.curriculum_v2.validators import (
    CurriculumNodeValidator,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-001E-1 - "
        "CURRICULUM NODE T2 CHANGE TEST"
    )
    print("=" * 72)

    validator = CurriculumNodeValidator()

    root = CurriculumNode(
        curriculum_node_id="CN-ROOT",
        curriculum_ref="CURR-001",
        code="ROOT",
        name="Toán 6",
        node_type="ROOT",
        sequence=1,
    )

    topic_a = CurriculumNode(
        curriculum_node_id="CN-TOPIC-A",
        curriculum_ref="CURR-001",
        code="TOPIC_A",
        name="Số và Đại số",
        node_type="CONTENT_STRAND",
        parent_id="CN-ROOT",
        sequence=1,
    )

    topic_b = CurriculumNode(
        curriculum_node_id="CN-TOPIC-B",
        curriculum_ref="CURR-001",
        code="TOPIC_B",
        name="Hình học và Đo lường",
        node_type="CONTENT_STRAND",
        parent_id="CN-ROOT",
        sequence=2,
    )

    # --------------------------------------------------------
    # 1. Đổi tên
    # --------------------------------------------------------

    renamed = replace(
        topic_a,
        name="Số học và Đại số",
    )

    assert validator.validate(
        renamed
    ).is_valid

    print(
        "Change name without core change: PASS"
    )

    # --------------------------------------------------------
    # 2. Đổi thứ tự
    # --------------------------------------------------------

    reordered = replace(
        topic_a,
        sequence=5,
    )

    assert validator.validate(
        reordered
    ).is_valid

    print(
        "Change sequence without core change: PASS"
    )

    # --------------------------------------------------------
    # 3. Đổi node_type
    # --------------------------------------------------------

    changed_type = replace(
        topic_a,
        node_type="NEW_FUTURE_NODE_TYPE",
    )

    assert validator.validate(
        changed_type
    ).is_valid

    print(
        "Change node type without core change: PASS"
    )

    # --------------------------------------------------------
    # 4. Đổi parent hợp lệ
    # --------------------------------------------------------

    moved_node = CurriculumNode(
        curriculum_node_id="CN-MOVED",
        curriculum_ref="CURR-001",
        code="MOVED",
        name="Nội dung di chuyển",
        node_type="CUSTOM",
        parent_id="CN-TOPIC-B",
        sequence=1,
    )

    relationship_result = (
        validator.validate_relationships(
            moved_node,
            existing_nodes=(
                root,
                topic_a,
                topic_b,
                moved_node,
            ),
        )
    )

    assert relationship_result.is_valid

    print(
        "Change parent through relationship: PASS"
    )

    # --------------------------------------------------------
    # 5. Bổ sung metadata
    # --------------------------------------------------------

    enriched = replace(
        topic_a,
        metadata={
            "source": "admin",
            "note": "Dữ liệu bổ sung",
            "future_field": "allowed",
        },
    )

    assert validator.validate(
        enriched
    ).is_valid

    assert (
        enriched.metadata[
            "future_field"
        ]
        == "allowed"
    )

    print(
        "Add metadata without schema change: PASS"
    )

    # --------------------------------------------------------
    # 6. Identity phải giữ ổn định
    # --------------------------------------------------------

    assert (
        renamed.curriculum_node_id
        == topic_a.curriculum_node_id
    )

    assert (
        reordered.curriculum_node_id
        == topic_a.curriculum_node_id
    )

    assert (
        changed_type.curriculum_node_id
        == topic_a.curriculum_node_id
    )

    print(
        "Stable identity preserved: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - T2 CHANGE VERIFIED"
    )


if __name__ == "__main__":
    main()