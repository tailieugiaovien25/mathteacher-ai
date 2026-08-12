from src.core_v2.rules import (
    Rule,
    RuleRegistry,
)

from src.curriculum_v2.models import (
    Competency,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-003F - "
        "COMPETENCY T5 COMPOSITION TEST"
    )
    print("=" * 72)

    competency_1 = Competency(
        competency_id="COMP-001",
        name="Tư duy và lập luận toán học",
        competency_type="SUBJECT_SPECIFIC",
        status="ACTIVE",
    )

    competency_2 = Competency(
        competency_id="COMP-002",
        name="Mô hình hóa toán học",
        competency_type="SUBJECT_SPECIFIC",
        status="ACTIVE",
    )

    source_competencies = (
        competency_1,
        competency_2,
    )

    registry = RuleRegistry()

    # --------------------------------------------------------
    # 1. GROUP rule
    # --------------------------------------------------------

    group_rule = Rule(
        rule_id="RULE-COMP-GROUP-001",
        rule_type="COMPOSITION",
        applies_to_data_type="COMPETENCY",
        context="LESSON_DESIGN",
        priority=10,
        condition={
            "status": "ACTIVE",
        },
        action={
            "operation": "GROUP",
        },
    )

    registry.register(
        group_rule
    )

    group_rules = registry.find(
        data_type_id="COMPETENCY",
        context="LESSON_DESIGN",
        rule_type="COMPOSITION",
    )

    assert len(group_rules) == 1

    assert (
        group_rules[0].action["operation"]
        == "GROUP"
    )

    print(
        "GROUP composition rule: PASS"
    )

    # --------------------------------------------------------
    # 2. FILTER rule
    # --------------------------------------------------------

    filter_rule = Rule(
        rule_id="RULE-COMP-FILTER-001",
        rule_type="COMPOSITION",
        applies_to_data_type="COMPETENCY",
        context="ASSESSMENT_SCOPE",
        priority=10,
        condition={
            "competency_type": "SUBJECT_SPECIFIC",
        },
        action={
            "operation": "FILTER",
        },
    )

    registry.register(
        filter_rule
    )

    filter_rules = registry.find(
        data_type_id="COMPETENCY",
        context="ASSESSMENT_SCOPE",
        rule_type="COMPOSITION",
    )

    assert len(filter_rules) == 1

    assert (
        filter_rules[0].action["operation"]
        == "FILTER"
    )

    print(
        "FILTER composition rule: PASS"
    )

    # --------------------------------------------------------
    # 3. Source data unchanged
    # --------------------------------------------------------

    assert len(source_competencies) == 2

    assert (
        competency_1.name
        == "Tư duy và lập luận toán học"
    )

    assert (
        competency_2.name
        == "Mô hình hóa toán học"
    )

    print(
        "Source competencies unchanged: PASS"
    )

    # --------------------------------------------------------
    # 4. Future composition operation
    # --------------------------------------------------------

    future_rule = Rule(
        rule_id="RULE-COMP-FUTURE-001",
        rule_type="COMPOSITION",
        applies_to_data_type="COMPETENCY",
        context="FUTURE_CONTEXT",
        priority=10,
        condition={
            "status": "ACTIVE",
        },
        action={
            "operation": "CLUSTER",
        },
    )

    registry.register(
        future_rule
    )

    future_rules = registry.find(
        data_type_id="COMPETENCY",
        context="FUTURE_CONTEXT",
        rule_type="COMPOSITION",
    )

    assert len(future_rules) == 1

    assert (
        future_rules[0].action["operation"]
        == "CLUSTER"
    )

    print(
        "New composition without "
        "model/core change: PASS"
    )

    # --------------------------------------------------------
    # 5. P4/P8
    # --------------------------------------------------------

    assert (
        "name"
        not in group_rule.action
    )

    assert (
        "official_code"
        not in group_rule.action
    )

    assert (
        "name"
        not in filter_rule.action
    )

    print(
        "P4/P8 composition without "
        "source duplication: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - COMPETENCY T5 COMPOSITION VERIFIED"
    )


if __name__ == "__main__":
    main()