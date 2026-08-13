from src.core_v2.mapping import (
    Mapping,
    MappingRegistry,
    MappingStatus,
)


def main():

    print("=" * 72)
    print(
        "V2-CORE-007 - "
        "MAPPING FOUNDATION TEST"
    )
    print("=" * 72)

    registry = MappingRegistry()

    mapping = Mapping(
        mapping_id="MAP-001",
        source_data_type="CURRICULUM",
        source_id="CURR-001",
        target_data_type="ACADEMIC_UNIT",
        target_id="AU-TOAN",
        mapping_type="CURRICULUM_UNIT",
        priority=10,
    )

    registry.register(mapping)

    assert len(registry.all()) == 1

    print(
        "Register mapping: PASS"
    )

    resolved = registry.get(
        "MAP-001"
    )

    assert resolved is mapping

    print(
        "Resolve mapping: PASS"
    )

    matches = registry.find_from(
        source_data_type="CURRICULUM",
        source_id="CURR-001",
        mapping_type="CURRICULUM_UNIT",
    )

    assert len(matches) == 1
    assert (
        matches[0].target_id
        == "AU-TOAN"
    )

    print(
        "Find mapping: PASS"
    )

    inactive_mapping = Mapping(
        mapping_id="MAP-002",
        source_data_type="CURRICULUM",
        source_id="CURR-001",
        target_data_type="ACADEMIC_UNIT",
        target_id="AU-OLD",
        mapping_type="CURRICULUM_UNIT",
        status=MappingStatus.INACTIVE,
        priority=1,
    )

    registry.register(
        inactive_mapping
    )

    matches = registry.find_from(
        source_data_type="CURRICULUM",
        source_id="CURR-001",
        mapping_type="CURRICULUM_UNIT",
    )

    assert len(matches) == 1
    assert matches[0].mapping_id == "MAP-001"

    print(
        "Inactive mapping ignored: PASS"
    )

    duplicate_blocked = False

    try:
        registry.register(mapping)

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate mapping blocked: PASS"
    )

    unknown_blocked = False

    try:
        registry.get(
            "UNKNOWN_MAPPING"
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print(
        "Unknown mapping blocked: PASS"
    )

    # P4 check:
    # Mapping chỉ giữ reference,
    # không giữ bản sao nội dung nguồn/đích.
    forbidden_fields = {
        "source_name",
        "source_content",
        "target_name",
        "target_content",
    }

    actual_fields = set(
        mapping.__dataclass_fields__
    )

    assert not (
        forbidden_fields
        & actual_fields
    )

    print(
        "P4 reference-only mapping: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - MAPPING FOUNDATION VERIFIED"
    )


if __name__ == "__main__":
    main()