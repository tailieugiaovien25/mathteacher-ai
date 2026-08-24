from datetime import date

import pytest

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)
from educational_planning_v2.models.teaching_assignment import (
    TeachingAssignment,
    TeachingAssignmentRole,
)
from educational_planning_v2.services.ppct_scope_resolver import (
    PPCTScopeMappingRule,
    PPCTScopeResolver,
)


def make_assignment(
    *,
    class_id="6A1",
    subject_ref="SUBJECT-A",
    component_ref=None,
):
    return TeachingAssignment(
        assignment_id="assignment-1",
        owner_id="teacher-1",
        academic_year="2026-2027",
        class_id=class_id,
        subject_ref=subject_ref,
        component_ref=component_ref,
        role=TeachingAssignmentRole.TEACHING,
        effective_from=date(2026, 9, 1),
        effective_to=date(2027, 5, 31),
    )


def test_resolves_rows_by_explicit_mapping():
    resolver = PPCTScopeResolver(
        rules=(
            PPCTScopeMappingRule(
                class_id="6A1",
                subject_ref="SUBJECT-A",
                subject_grade="SOURCE-GRADE-A",
                sub_subject="COMPONENT-A",
            ),
        )
    )

    result = resolver.resolve(
        make_assignment(),
        (
            PPCTRow(
                subject_grade="SOURCE-GRADE-A",
                sub_subject="COMPONENT-A",
                period=1,
                lesson_name="Lesson 1",
            ),
            PPCTRow(
                subject_grade="SOURCE-GRADE-B",
                sub_subject="COMPONENT-A",
                period=1,
                lesson_name="Other lesson",
            ),
        ),
    )

    assert len(result) == 1
    assert result[0].lesson_name == "Lesson 1"


def test_component_assignment_mapping_is_supported():
    resolver = PPCTScopeResolver(
        rules=(
            PPCTScopeMappingRule(
                class_id="8A1",
                subject_ref="SUBJECT-A",
                component_ref="COMPONENT-REF-A",
                subject_grade="SOURCE-GRADE-A",
                sub_subject="SOURCE-COMPONENT-A",
            ),
        )
    )

    result = resolver.resolve(
        make_assignment(
            class_id="8A1",
            component_ref="COMPONENT-REF-A",
        ),
        (
            PPCTRow(
                subject_grade="SOURCE-GRADE-A",
                sub_subject="SOURCE-COMPONENT-A",
                period=1,
                lesson_name="Lesson 1",
            ),
        ),
    )

    assert len(result) == 1


def test_missing_mapping_is_reported():
    resolver = PPCTScopeResolver(
        rules=()
    )

    with pytest.raises(
        LookupError,
        match="PPCT scope mapping not found",
    ):
        resolver.resolve(
            make_assignment(),
            (),
        )


def test_duplicate_assignment_mapping_is_rejected():
    rule = PPCTScopeMappingRule(
        class_id="6A1",
        subject_ref="SUBJECT-A",
        subject_grade="SOURCE-A",
    )

    with pytest.raises(
        ValueError,
        match="duplicate PPCT scope mapping",
    ):
        PPCTScopeResolver(
            rules=(
                rule,
                rule,
            )
        )


def test_mapping_rule_normalizes_text():
    rule = PPCTScopeMappingRule(
        class_id=" 6A1 ",
        subject_ref=" SUBJECT-A ",
        subject_grade=" SOURCE-A ",
        component_ref=" ",
        sub_subject=" ",
    )

    assert rule.class_id == "6A1"
    assert rule.subject_ref == "SUBJECT-A"
    assert rule.subject_grade == "SOURCE-A"
    assert rule.component_ref is None
    assert rule.sub_subject is None


def test_resolver_rejects_non_tuple_rows():
    resolver = PPCTScopeResolver(
        rules=(
            PPCTScopeMappingRule(
                class_id="6A1",
                subject_ref="SUBJECT-A",
                subject_grade="SOURCE-A",
            ),
        )
    )

    with pytest.raises(
        TypeError,
        match="rows must be a tuple",
    ):
        resolver.resolve(
            make_assignment(),
            [],
        )
