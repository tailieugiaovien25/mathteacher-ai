from src.core_v2.rules import (
    Rule,
    RuleRegistry,
    RuleStatus,
)


def main():
    print("=" * 72)
    print(
        "V2-CORE-005 - "
        "RULE REGISTRY TEST"
    )
    print("=" * 72)

    registry = RuleRegistry()

    merge_rule = Rule(
        rule_id="RULE-AU-MERGE-001",
        rule_type="COMPOSITION",
        applies_to_data_type="ACADEMIC_UNIT",
        context="SUBJECT_SUMMARY",
        priority=10,
        condition={
            "parent_code": "TOAN",
        },
        action={
            "operation": "MERGE",
        },
    )

    split_rule = Rule(
        rule_id="RULE-AU-SPLIT-001",
        rule_type="COMPOSITION",
        applies_to_data_type="ACADEMIC_UNIT",
        context="TIMETABLE",
        priority=10,
        condition={
            "parent_code": "TOAN",
        },
        action={
            "operation": "SPLIT",
        },
    )

    inactive_rule = Rule(
        rule_id="RULE-INACTIVE-001",
        rule_type="COMPOSITION",
        applies_to_data_type="ACADEMIC_UNIT",
        context="TIMETABLE",
        priority=1,
        status=RuleStatus.INACTIVE,
        action={
            "operation": "IGNORE",
        },
    )

    registry.register(merge_rule)
    registry.register(split_rule)
    registry.register(inactive_rule)

    assert len(registry.all()) == 3
    assert len(registry.active()) == 2

    print(
        "Register rules: PASS"
    )

    subject_rules = registry.find(
        data_type_id="ACADEMIC_UNIT",
        context="SUBJECT_SUMMARY",
        rule_type="COMPOSITION",
    )

    assert len(subject_rules) == 1
    assert (
        subject_rules[0].action["operation"]
        == "MERGE"
    )

    print(
        "Context MERGE rule: PASS"
    )

    timetable_rules = registry.find(
        data_type_id="ACADEMIC_UNIT",
        context="TIMETABLE",
        rule_type="COMPOSITION",
    )

    assert len(timetable_rules) == 1
    assert (
        timetable_rules[0].action["operation"]
        == "SPLIT"
    )

    print(
        "Context SPLIT rule: PASS"
    )

    duplicate_blocked = False

    try:
        registry.register(
            merge_rule
        )

    except ValueError:
        duplicate_blocked = True

    assert duplicate_blocked

    print(
        "Duplicate rule blocked: PASS"
    )

    unknown_blocked = False

    try:
        registry.get(
            "UNKNOWN_RULE"
        )

    except KeyError:
        unknown_blocked = True

    assert unknown_blocked

    print(
        "Unknown rule blocked: PASS"
    )

    print()

    print(
        "RESULT: "
        "PASS - RULE REGISTRY VERIFIED"
    )


if __name__ == "__main__":
    main()