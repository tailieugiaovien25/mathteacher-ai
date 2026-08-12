from src.curriculum_v2.models import (
    CurriculumNode,
)

from src.curriculum_v2.validators import (
    CurriculumNodeValidator,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-001C - "
        "CURRICULUM NODE TEST"
    )
    print("=" * 72)

    validator = (
        CurriculumNodeValidator()
    )

    root = CurriculumNode(
        curriculum_node_id="CN-ROOT",
        curriculum_ref="CURR-001",
        code="ROOT",
        name="Toán 6",
        node_type="ROOT",
        sequence=1,
    )

    topic = CurriculumNode(
        curriculum_node_id="CN-TOPIC-001",
        curriculum_ref="CURR-001",
        code="SO_DAI_SO",
        name="Số và Đại số",
        node_type="CONTENT_STRAND",
        parent_id="CN-ROOT",
        sequence=1,
    )

    lesson = CurriculumNode(
        curriculum_node_id="CN-LESSON-001",
        curriculum_ref="CURR-001",
        code="BAI_001",
        name="Bài 1",
        node_type="LESSON",
        parent_id="CN-TOPIC-001",
        sequence=1,
    )

    assert validator.validate(
        root
    ).is_valid

    assert validator.validate(
        topic
    ).is_valid

    assert validator.validate(
        lesson
    ).is_valid

    print(
        "T1 ADD / basic structure: PASS"
    )

    relationship_result = (
        validator.validate_relationships(
            lesson,
            existing_nodes=(
                root,
                topic,
                lesson,
            ),
        )
    )

    assert relationship_result.is_valid

    print(
        "T3 valid relationship: PASS"
    )

    self_parent = CurriculumNode(
        curriculum_node_id="CN-BAD",
        curriculum_ref="CURR-001",
        code="BAD",
        name="Bad Node",
        node_type="CUSTOM_TYPE",
        parent_id="CN-BAD",
        sequence=1,
    )

    result = validator.validate(
        self_parent
    )

    assert not result.is_valid

    print(
        "T7 self-parent blocked: PASS"
    )

    missing_parent = CurriculumNode(
        curriculum_node_id="CN-MISSING",
        curriculum_ref="CURR-001",
        code="MISSING",
        name="Missing Parent",
        node_type="CUSTOM_TYPE",
        parent_id="UNKNOWN",
        sequence=1,
    )

    result = (
        validator.validate_relationships(
            missing_parent,
            existing_nodes=(
                root,
                topic,
                lesson,
                missing_parent,
            ),
        )
    )

    assert not result.is_valid

    print(
        "T7 missing parent blocked: PASS"
    )

    # --------------------------------------------------------
    # Cycle test:
    # A -> B -> A
    # --------------------------------------------------------

    node_a = CurriculumNode(
        curriculum_node_id="CN-A",
        curriculum_ref="CURR-001",
        code="A",
        name="Node A",
        node_type="CUSTOM_TYPE",
        parent_id="CN-B",
    )

    node_b = CurriculumNode(
        curriculum_node_id="CN-B",
        curriculum_ref="CURR-001",
        code="B",
        name="Node B",
        node_type="CUSTOM_TYPE",
        parent_id="CN-A",
    )

    result = (
        validator.validate_relationships(
            node_a,
            existing_nodes=(
                node_a,
                node_b,
            ),
        )
    )

    assert not result.is_valid

    print(
        "T7 cycle blocked: PASS"
    )

    # --------------------------------------------------------
    # P1 test:
    # loại node mới không cần sửa model/validator
    # --------------------------------------------------------

    custom_node = CurriculumNode(
        curriculum_node_id="CN-CUSTOM",
        curriculum_ref="CURR-001",
        code="CUSTOM",
        name="Loại nội dung mới",
        node_type="NEW_FUTURE_TYPE",
        parent_id="CN-ROOT",
    )

    assert validator.validate(
        custom_node
    ).is_valid

    assert (
        validator.validate_relationships(
            custom_node,
            existing_nodes=(
                root,
                custom_node,
            ),
        ).is_valid
    )

    print(
        "P1 new node type without "
        "core change: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - CURRICULUM NODE VERIFIED"
    )


if __name__ == "__main__":
    main()