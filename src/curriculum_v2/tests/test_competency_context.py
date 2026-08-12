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
        "V2-MODULE-003E - "
        "COMPETENCY T4 CONTEXT TEST"
    )
    print("=" * 72)

    competency = Competency(
        competency_id="COMP-001",
        name="Tư duy và lập luận toán học",
        competency_type="SUBJECT_SPECIFIC",
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
            "USE_FOR_LESSON_DESIGN",
        ),
        (
            "LESSON_PRESENTATION",
            "USE_FOR_PRESENTATION_DESIGN",
        ),
        (
            "LEARNING_MATERIAL",
            "USE_FOR_MATERIAL_DESIGN",
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
                rule_id=f"RULE-COMP-{index:03d}",
                rule_type="ROUTING",
                applies_to_data_type="COMPETENCY",
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
    # 1. Kiểm tra từng context
    # --------------------------------------------------------

    for (
        context_name,
        expected_operation,
    ) in contexts:

        rules = registry.find(
            data_type_id="COMPETENCY",
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
    # 2. Source data không thay đổi
    # --------------------------------------------------------

    assert competency.competency_id == "COMP-001"
    assert (
        competency.name
        == "Tư duy và lập luận toán học"
    )
    assert (
        competency.competency_type
        == "SUBJECT_SPECIFIC"
    )

    print(
        "Source competency unchanged: PASS"
    )

    # --------------------------------------------------------
    # 3. Context mới trong tương lai
    # --------------------------------------------------------

    registry.register(
        Rule(
            rule_id="RULE-COMP-FUTURE",
            rule_type="ROUTING",
            applies_to_data_type="COMPETENCY",
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
        data_type_id="COMPETENCY",
        context="FUTURE_PRODUCT",
        rule_type="ROUTING",
    )

    assert len(future_rules) == 1

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
        "PASS - COMPETENCY T4 CONTEXT VERIFIED"
    )


if __name__ == "__main__":
    main()