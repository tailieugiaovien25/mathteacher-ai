from src.core_v2.mapping import (
    Mapping,
    MappingRegistry,
)

from src.curriculum_v2.models import (
    LearningOutcome,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-002C - "
        "LEARNING OUTCOME T3 RELATIONSHIP TEST"
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

    registry = MappingRegistry()

    # --------------------------------------------------------
    # 1. YCCD -> CURRICULUM_NODE
    # --------------------------------------------------------

    node_mapping = Mapping(
        mapping_id="MAP-LO-NODE-001",
        source_data_type="LEARNING_OUTCOME",
        source_id=outcome.learning_outcome_id,
        target_data_type="CURRICULUM_NODE",
        target_id="CN-LESSON-001",
        mapping_type="OUTCOME_TO_NODE",
        priority=10,
    )

    registry.register(
        node_mapping
    )

    node_matches = registry.find_from(
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        mapping_type="OUTCOME_TO_NODE",
    )

    assert len(node_matches) == 1

    assert (
        node_matches[0].target_id
        == "CN-LESSON-001"
    )

    print(
        "YCCD -> CURRICULUM_NODE mapping: PASS"
    )

    # --------------------------------------------------------
    # 2. YCCD -> ACADEMIC_UNIT
    # --------------------------------------------------------

    academic_mapping = Mapping(
        mapping_id="MAP-LO-AU-001",
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        target_data_type="ACADEMIC_UNIT",
        target_id="AU-TOAN",
        mapping_type="OUTCOME_TO_ACADEMIC_UNIT",
        priority=10,
    )

    registry.register(
        academic_mapping
    )

    academic_matches = registry.find_from(
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        mapping_type="OUTCOME_TO_ACADEMIC_UNIT",
    )

    assert len(academic_matches) == 1

    assert (
        academic_matches[0].target_id
        == "AU-TOAN"
    )

    print(
        "YCCD -> ACADEMIC_UNIT mapping: PASS"
    )

    # --------------------------------------------------------
    # 3. YCCD -> GRADE_LEVEL
    # --------------------------------------------------------

    grade_mapping = Mapping(
        mapping_id="MAP-LO-GL-001",
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        target_data_type="GRADE_LEVEL",
        target_id="GL06",
        mapping_type="OUTCOME_TO_GRADE_LEVEL",
        priority=10,
    )

    registry.register(
        grade_mapping
    )

    grade_matches = registry.find_from(
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        mapping_type="OUTCOME_TO_GRADE_LEVEL",
    )

    assert len(grade_matches) == 1

    assert (
        grade_matches[0].target_id
        == "GL06"
    )

    print(
        "YCCD -> GRADE_LEVEL mapping: PASS"
    )

    # --------------------------------------------------------
    # 4. Thay đổi relationship
    #    không sửa YCCD
    # --------------------------------------------------------

    new_node_mapping = Mapping(
        mapping_id="MAP-LO-NODE-002",
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        target_data_type="CURRICULUM_NODE",
        target_id="CN-LESSON-002",
        mapping_type="OUTCOME_TO_NODE",
        priority=20,
    )

    registry.register(
        new_node_mapping
    )

    node_matches = registry.find_from(
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
        mapping_type="OUTCOME_TO_NODE",
    )

    assert len(node_matches) == 2

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
        "Relationship change without "
        "YCCD change: PASS"
    )

    # --------------------------------------------------------
    # 5. P4:
    # Mapping không được sao chép nội dung YCCD
    # --------------------------------------------------------

    mapping_fields = set(
        node_mapping.__dataclass_fields__
    )

    forbidden_fields = {
        "statement",
        "source_statement",
        "learning_outcome_statement",
        "target_content",
    }

    assert not (
        mapping_fields
        & forbidden_fields
    )

    print(
        "P4 reference-only relationship: PASS"
    )

    # --------------------------------------------------------
    # 6. Một YCCD có thể có nhiều quan hệ
    # --------------------------------------------------------

    all_from_outcome = registry.find_from(
        source_data_type="LEARNING_OUTCOME",
        source_id="LO-001",
    )

    assert len(
        all_from_outcome
    ) == 4

    print(
        "Multiple relationships supported: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - T3 RELATIONSHIP VERIFIED"
    )


if __name__ == "__main__":
    main()