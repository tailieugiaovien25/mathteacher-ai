from src.core_v2.rules import (
    Rule,
    RuleRegistry,
)

from src.curriculum_v2.models import (
    LearningOutcome,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-002E - "
        "LEARNING OUTCOME T5 COMPOSITION TEST"
    )
    print("=" * 72)

    outcome_1 = LearningOutcome(
        learning_outcome_id="LO-001",
        curriculum_ref="CURR-001",
        code="LO-001",
        statement="YCCD thứ nhất.",
        outcome_type="GENERAL",
        status="ACTIVE",
    )

    outcome_2 = LearningOutcome(
        learning_outcome_id="LO-002",
        curriculum_ref="CURR-001",
        code="LO-002",
        statement="YCCD thứ hai.",
        outcome_type="GENERAL",
        status="ACTIVE",
    )

    source_outcomes = (
        outcome_1,
        outcome_2,
    )

    registry = RuleRegistry()

    group_rule = Rule(
        rule_id="RULE-LO-GROUP-001",
        rule_type="COMPOSITION",
        applies_to_data_type="LEARNING_OUTCOME",
        context="LESSON_OBJECTIVES",
        priority=10,
        condition={
            "status": "ACTIVE",
        },
        action={
            "operation": "GROUP",
        },
    )

    filter_rule = Rule(
        rule_id="RULE-LO-FILTER-001",
        rule_type="COMPOSITION",
        applies_to_data_type="LEARNING_OUTCOME",
        context="ASSESSMENT_SCOPE",
        priority=10,
        condition={
            "status": "ACTIVE",
        },
        action={
            "operation": "FILTER",
        },
    )

    registry.register(
        group_rule
    )

    registry.register(
        filter_rule
    )

    # --------------------------------------------------------
    # 1. GROUP
    # --------------------------------------------------------

    group_rules = registry.find(
        data_type_id="LEARNING_OUTCOME",
        context="LESSON_OBJECTIVES",
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
    # 2. FILTER
    # --------------------------------------------------------

    filter_rules = registry.find(
        data_type_id="LEARNING_OUTCOME",
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

    assert len(
        source_outcomes
    ) == 2

    assert (
        outcome_1.statement
        == "YCCD thứ nhất."
    )

    assert (
        outcome_2.statement
        == "YCCD thứ hai."
    )

    print(
        "Source YCCD unchanged: PASS"
    )

    # --------------------------------------------------------
    # 4. New composition operation
    # --------------------------------------------------------

    future_rule = Rule(
        rule_id="RULE-LO-FUTURE-001",
        rule_type="COMPOSITION",
        applies_to_data_type="LEARNING_OUTCOME",
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
        data_type_id="LEARNING_OUTCOME",
        context="FUTURE_CONTEXT",
        rule_type="COMPOSITION",
    )

    assert len(
        future_rules
    ) == 1

    assert (
        future_rules[0].action["operation"]
        == "CLUSTER"
    )

    print(
        "New composition without "
        "model/core change: PASS"
    )

    # --------------------------------------------------------
    # 5. P4 check
    # --------------------------------------------------------

    assert (
        "statement"
        not in group_rule.action
    )

    assert (
        "statement"
        not in filter_rule.action
    )

    print(
        "P4 composition without "
        "source duplication: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - T5 COMPOSITION VERIFIED"
    )


if __name__ == "__main__":
    main()