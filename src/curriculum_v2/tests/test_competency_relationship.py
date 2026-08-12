from src.core_v2.mapping import (
    Mapping,
    MappingRegistry,
)

from src.curriculum_v2.models import (
    Competency,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-003D - "
        "COMPETENCY T3 RELATIONSHIP TEST"
    )
    print("=" * 72)

    competency = Competency(
        competency_id="COMP-001",
        name="Tư duy và lập luận toán học",
        competency_type="SUBJECT_SPECIFIC",
        status="ACTIVE",
    )

    registry = MappingRegistry()

    # 1. COMPETENCY -> LEARNING_OUTCOME
    lo_mapping = Mapping(
        mapping_id="MAP-COMP-LO-001",
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        target_data_type="LEARNING_OUTCOME",
        target_id="LO-001",
        mapping_type="COMPETENCY_TO_OUTCOME",
        priority=10,
    )

    registry.register(
        lo_mapping
    )

    lo_matches = registry.find_from(
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        mapping_type="COMPETENCY_TO_OUTCOME",
    )

    assert len(lo_matches) == 1
    assert lo_matches[0].target_id == "LO-001"

    print(
        "COMPETENCY -> LEARNING_OUTCOME: PASS"
    )

    # 2. COMPETENCY -> CURRICULUM_NODE
    node_mapping = Mapping(
        mapping_id="MAP-COMP-NODE-001",
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        target_data_type="CURRICULUM_NODE",
        target_id="CN-001",
        mapping_type="COMPETENCY_TO_NODE",
        priority=10,
    )

    registry.register(
        node_mapping
    )

    node_matches = registry.find_from(
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        mapping_type="COMPETENCY_TO_NODE",
    )

    assert len(node_matches) == 1
    assert node_matches[0].target_id == "CN-001"

    print(
        "COMPETENCY -> CURRICULUM_NODE: PASS"
    )

    # 3. COMPETENCY -> ACADEMIC_UNIT
    academic_mapping = Mapping(
        mapping_id="MAP-COMP-AU-001",
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        target_data_type="ACADEMIC_UNIT",
        target_id="AU-TOAN",
        mapping_type="COMPETENCY_TO_ACADEMIC_UNIT",
        priority=10,
    )

    registry.register(
        academic_mapping
    )

    academic_matches = registry.find_from(
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        mapping_type="COMPETENCY_TO_ACADEMIC_UNIT",
    )

    assert len(academic_matches) == 1
    assert academic_matches[0].target_id == "AU-TOAN"

    print(
        "COMPETENCY -> ACADEMIC_UNIT: PASS"
    )

    # 4. COMPETENCY -> COMPETENCY
    component_mapping = Mapping(
        mapping_id="MAP-COMP-COMP-001",
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        target_data_type="COMPETENCY",
        target_id="COMP-002",
        mapping_type="HAS_COMPONENT",
        priority=10,
    )

    registry.register(
        component_mapping
    )

    component_matches = registry.find_from(
        source_data_type="COMPETENCY",
        source_id="COMP-001",
        mapping_type="HAS_COMPONENT",
    )

    assert len(component_matches) == 1
    assert component_matches[0].target_id == "COMP-002"

    print(
        "COMPETENCY -> COMPETENCY relationship: PASS"
    )

    # 5. Source competency unchanged
    assert competency.competency_id == "COMP-001"
    assert competency.name == "Tư duy và lập luận toán học"

    print(
        "Source competency unchanged: PASS"
    )

    # 6. P4/P8:
    # Mapping chỉ giữ reference, không sao chép tên/mã.
    fields = set(
        lo_mapping.__dataclass_fields__
    )

    forbidden = {
        "competency_name",
        "official_code",
        "source_content",
        "target_content",
    }

    assert not (
        fields
        & forbidden
    )

    print(
        "P4/P8 reference-only relationship: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - COMPETENCY T3 RELATIONSHIP VERIFIED"
    )


if __name__ == "__main__":
    main()