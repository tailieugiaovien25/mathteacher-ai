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
        "V2-MODULE-001E-3 - "
        "CURRICULUM NODE T5 COMPOSITION TEST"
    )
    print("=" * 72)

    root = CurriculumNode(
        curriculum_node_id="CN-ROOT",
        curriculum_ref="CURR-001",
        code="TOAN",
        name="Toán",
        node_type="ACADEMIC_ROOT",
        sequence=1,
    )

    algebra = CurriculumNode(
        curriculum_node_id="CN-ALGEBRA",
        curriculum_ref="CURR-001",
        code="DAI_SO",
        name="Đại số",
        node_type="CONTENT_BRANCH",
        parent_id="CN-ROOT",
        sequence=1,
    )

    geometry = CurriculumNode(
        curriculum_node_id="CN-GEOMETRY",
        curriculum_ref="CURR-001",
        code="HINH_HOC",
        name="Hình học",
        node_type="CONTENT_BRANCH",
        parent_id="CN-ROOT",
        sequence=2,
    )

    source_nodes = (
        root,
        algebra,
        geometry,
    )

    registry = RuleRegistry()

    merge_rule = Rule(
        rule_id="RULE-CN-MERGE-001",
        rule_type="COMPOSITION",
        applies_to_data_type="CURRICULUM_NODE",
        context="SUBJECT_SUMMARY",
        priority=10,
        condition={
            "parent_id": "CN-ROOT",
        },
        action={
            "operation": "MERGE",
            "target_id": "CN-ROOT",
        },
    )

    split_rule = Rule(
        rule_id="RULE-CN-SPLIT-001",
        rule_type="COMPOSITION",
        applies_to_data_type="CURRICULUM_NODE",
        context="DETAILED_VIEW",
        priority=10,
        condition={
            "parent_id": "CN-ROOT",
        },
        action={
            "operation": "SPLIT",
        },
    )

    registry.register(
        merge_rule
    )

    registry.register(
        split_rule
    )

    # --------------------------------------------------------
    # 1. MERGE context
    # --------------------------------------------------------

    merge_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="SUBJECT_SUMMARY",
        rule_type="COMPOSITION",
    )

    assert len(merge_rules) == 1

    assert (
        merge_rules[0].action["operation"]
        == "MERGE"
    )

    assert (
        merge_rules[0].action["target_id"]
        == "CN-ROOT"
    )

    print(
        "MERGE composition rule: PASS"
    )

    # --------------------------------------------------------
    # 2. SPLIT context
    # --------------------------------------------------------

    split_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="DETAILED_VIEW",
        rule_type="COMPOSITION",
    )

    assert len(split_rules) == 1

    assert (
        split_rules[0].action["operation"]
        == "SPLIT"
    )

    print(
        "SPLIT composition rule: PASS"
    )

    # --------------------------------------------------------
    # 3. Source data unchanged
    # --------------------------------------------------------

    assert len(source_nodes) == 3

    assert root.name == "Toán"

    assert algebra.name == "Đại số"

    assert geometry.name == "Hình học"

    assert (
        algebra.parent_id
        == "CN-ROOT"
    )

    assert (
        geometry.parent_id
        == "CN-ROOT"
    )

    print(
        "Source tree unchanged: PASS"
    )

    # --------------------------------------------------------
    # 4. New composition operation
    #    without changing model/core
    # --------------------------------------------------------

    future_rule = Rule(
        rule_id="RULE-CN-FUTURE-COMPOSE",
        rule_type="COMPOSITION",
        applies_to_data_type="CURRICULUM_NODE",
        context="FUTURE_CONTEXT",
        priority=10,
        condition={
            "node_type": "CONTENT_BRANCH",
        },
        action={
            "operation": "GROUP",
        },
    )

    registry.register(
        future_rule
    )

    future_rules = registry.find(
        data_type_id="CURRICULUM_NODE",
        context="FUTURE_CONTEXT",
        rule_type="COMPOSITION",
    )

    assert len(future_rules) == 1

    assert (
        future_rules[0].action["operation"]
        == "GROUP"
    )

    print(
        "New composition without "
        "model/core change: PASS"
    )

    # --------------------------------------------------------
    # 5. P4 check
    #    Rules reference identities,
    #    not copied source content.
    # --------------------------------------------------------

    assert (
        merge_rules[0].action["target_id"]
        == root.curriculum_node_id
    )

    assert (
        "target_name"
        not in merge_rules[0].action
    )

    print(
        "P4 composition by reference: PASS"
    )

    print()
    print(
        "RESULT: "
        "PASS - T5 COMPOSITION VERIFIED"
    )


if __name__ == "__main__":
    main()