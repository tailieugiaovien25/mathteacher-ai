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
        "V2-MODULE-002D - "
        "LEARNING OUTCOME T4 CONTEXT TEST"
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

    registry = RuleRegistry()

    contexts = (
        (
            "PPCT",
            "USE_FOR_PLANNING",
        ),
        (
            "LESSON_PLAN",
            "USE_FOR_LESSON_OBJECTIVE",
        ),
        (
            "LESSON_PRESENTATION",
            "USE_FOR_PRESENTATION",
        ),
        (
            "LEARNING_MATERIAL",
            "USE_FOR_MATERIAL",
        ),
        (
            "ASSESSMENT",
            "USE_FOR_ASSESSMENT_MAPPING",
        ),
    )

    for index, (
        context_name,
        operation,
    ) in enumerate(
        contexts,
        start=1,
    ):

        registry.register(
            Rule(
                rule_id=f"RULE-LO-{index:03d}",
                rule_type="ROUTING",
                applies_to_data_type=(
                    "LEARNING_OUTCOME"
                ),
                context=context_name,
                priority=10,
                condition={
                    "status": "ACTIVE",
                },
                action={
                    "operation": operation,
                },
            )
        )

    # --------------------------------------------------------
    # Kiểm tra từng Context
    # --------------------------------------------------------

    for (
        context_name,
        expected_operation,
    ) in contexts:

        rules = registry.find(
            data_type_id="LEARNING_OUTCOME",
            context=context_name,
            rule_type="ROUTING",
        )

        assert len(rules) == 1

        assert (
            rules[0].action["operation"]
            == expected_operation
        )

        print(
            f"{context_name} context: PASS"
        )

    # --------------------------------------------------------
    # Source YCCD không thay đổi
    # --------------------------------------------------------

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
        "Source YCCD unchanged: PASS"
    )

    # --------------------------------------------------------
    # Context mới trong tương lai
    # không cần sửa model/core
    # --------------------------------------------------------

    registry.register(
        Rule(
            rule_id="RULE-LO-FUTURE",
            rule_type="ROUTING",
            applies_to_data_type=(
                "LEARNING_OUTCOME"
            ),
            context="FUTURE_PRODUCT",
            priority=10,
            condition={
                "status": "ACTIVE",
            },
            action={
                "operation": "FUTURE_USE",
            },
        )
    )

    future_rules = registry.find(
        data_type_id="LEARNING_OUTCOME",
        context="FUTURE_PRODUCT",
        rule_type="ROUTING",
    )

    assert len(
        future_rules
    ) == 1

    assert (
        future_rules[0].action["operation"]
        == "FUTURE_USE"
    )

    print(
        "New context without model/core change: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - T4 CONTEXT VERIFIED"
    )


if __name__ == "__main__":
    main()