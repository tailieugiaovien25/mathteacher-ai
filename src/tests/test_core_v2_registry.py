from src.core_v2.registry import (
    DEFAULT_PASSPORTS,
    DataTypeRegistry,
    DataTypeStatus,
)


def main():
    print("=" * 72)
    print(
        "V2-CORE-003 - "
        "DATA TYPE REGISTRY TEST"
    )
    print("=" * 72)

    registry = DataTypeRegistry()

    registry.register_many(
        DEFAULT_PASSPORTS
    )

    all_items = registry.all()
    accepted_items = registry.accepted()

    print(
        "Registered:",
        len(all_items),
    )

    print(
        "Accepted:",
        len(accepted_items),
    )

    print()

    expected_ids = {
        "ACADEMIC_UNIT",
        "GRADE_LEVEL",
        "CLASS_GROUP",
        "TEACHER",
        "CURRICULUM",
    }

    actual_ids = {
        item.data_type_id
        for item in all_items
    }

    assert actual_ids == expected_ids
    assert len(all_items) == 5
    assert len(accepted_items) == 5

    for item in accepted_items:
        assert (
            item.status
            == DataTypeStatus.ACCEPTED
        )

        assert item.required_fields

        print(
            f"{item.data_type_id}: "
            f"ACCEPTED | "
            f"family={item.family} | "
            f"capabilities="
            f"{len(item.supported_capabilities)}"
        )

    print()

    # Duplicate registration must fail closed.
    duplicate_blocked = False

    try:
        registry.register(
            DEFAULT_PASSPORTS[0]
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked is True

    # Unknown Data Type must fail closed.
    unknown_blocked = False

    try:
        registry.get(
            "UNKNOWN_DATA_TYPE"
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked is True

    print(
        "Duplicate registration: PASS"
    )

    print(
        "Unknown Data Type: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - CORE V2 REGISTRY VERIFIED"
    )


if __name__ == "__main__":
    main()