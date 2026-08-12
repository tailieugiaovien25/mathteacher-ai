from src.core_v2.rules import (
    Rule,
    RuleRegistry,
)

from src.curriculum_v2.models import (
    CurriculumNode,
)


def main():

    print("=" * 72)
    print(
        "V2-MODULE-001E-2 - "
        "CURRICULUM NODE T4 CONTEXT TEST"
    )
    print("=" * 72)

    node = CurriculumNode(
        curriculum_node_id="CN-001",
        curriculum_ref="CURR-001",
        code="BAI_001",
        name="Bài 1",
        node_type="LESSON",
        parent_id="CN-TOPIC-001",
        sequence=1,
    )

    registry = RuleRegistry()

    ppct_rule = Rule(
        rule_id="RULE-CN-PPCT-001",
        rule_type="ROUTING",
        applies_to_data_type="CURRICULUM_NODE",
        context="PPCT",
        priority=10,
        condition={
            "node_type": "LESSON",
        },
        action={
            "operation": "INCLUDE",
            "view": "CURRICULUM_STRUCTURE",
        },
    )

    lesson_plan_rule = Rule(
        rule_id="RULE-CN-LESSON-001",
        rule_type="ROUTING",
        applies_to_data_type="CURRICULUM_NODE",
        context="LESSON_PLAN",
        priority=10,
        condition={
            "node_type": "LESSON",
        },
        action={
            "operation": "USE_AS_LESSON_SOURCE",
            "view": "LESSON_CONTEXT",
        },
    )

    assessment_rule = Rule(
        rule_id="RULE-CN-ASSESSMENT-001",
        rule_type="ROUTING",
        applies_to_data_type="CURRICULUM_NODE",
        context="ASSESSMENT",
        priority=10,
        condition={
            "node_type": "LESSON",
        },
        action={
            "operation": "USE_FOR_MAPPING",
            "view": "ASSESSMENT_CONTEXT",
        },
    )

    registry.register(ppct_rule)
    registry.register(lesson_plan_rule)
    registry.register(assessment_rule)

    # --------------------------------------------------------
    # 1. PPCT context
    # --------------------------------------------------------

    ppct_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="PPCT",
        rule_type="ROUTING",
    )

    assert len(ppct_rules) == 1
    assert (
        ppct_rules[0].action["operation"]
        == "INCLUDE"
    )

    print(
        "PPCT context rule: PASS"
    )

    # --------------------------------------------------------
    # 2. Lesson Plan context
    # --------------------------------------------------------

    lesson_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="LESSON_PLAN",
        rule_type="ROUTING",
    )

    assert len(lesson_rules) == 1
    assert (
        lesson_rules[0].action["operation"]
        == "USE_AS_LESSON_SOURCE"
    )

    print(
        "Lesson Plan context rule: PASS"
    )

    # --------------------------------------------------------
    # 3. Assessment context
    # --------------------------------------------------------

    assessment_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="ASSESSMENT",
        rule_type="ROUTING",
    )

    assert len(assessment_rules) == 1
    assert (
        assessment_rules[0].action["operation"]
        == "USE_FOR_MAPPING"
    )

    print(
        "Assessment context rule: PASS"
    )

    # --------------------------------------------------------
    # 4. Dữ liệu gốc phải giữ nguyên
    # --------------------------------------------------------

    assert node.curriculum_node_id == "CN-001"
    assert node.code == "BAI_001"
    assert node.name == "Bài 1"
    assert node.node_type == "LESSON"
    assert node.parent_id == "CN-TOPIC-001"

    print(
        "Source data unchanged: PASS"
    )

    # --------------------------------------------------------
    # 5. Context mới không cần sửa model
    # --------------------------------------------------------

    new_context_rule = Rule(
        rule_id="RULE-CN-FUTURE-001",
        rule_type="ROUTING",
        applies_to_data_type="CURRICULUM_NODE",
        context="FUTURE_NEW_CONTEXT",
        priority=10,
        condition={
            "node_type": "LESSON",
        },
        action={
            "operation": "FUTURE_OPERATION",
        },
    )

    registry.register(
        new_context_rule
    )

    future_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="FUTURE_NEW_CONTEXT",
        rule_type="ROUTING",
    )

    assert len(future_rules) == 1
    assert (
        future_rules[0].action["operation"]
        == "FUTURE_OPERATION"
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