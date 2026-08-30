from datetime import datetime, timezone

import pytest

from portal_v2.context.models import SystemContext
from portal_v2.context.runtime_context_bridge import (
    apply_runtime_context_bundle,
    apply_runtime_context_change,
)


NOW = datetime.now(timezone.utc)


def populated():
    return SystemContext(
        user_id="u1",
        academic_year="2026-2027",
        week_number=2,
        subject_ref="MATH",
        component_ref="ALGEBRA",
        grade=6,
        class_id="6A1",
        timetable_slot_id="slot-1",
        teaching_date="2026-09-14",
        timetable_period=1,
        curriculum_period=10,
        lesson_id="lesson-10",
        source_page="old",
        source_control="old",
        context_version=3,
    )


def test_subject_change_invalidates_descendants():
    out = apply_runtime_context_change(
        current=populated(),
        field="subject_ref",
        value="ENGLISH",
        source_page="standardization",
        source_control="subject",
        occurred_at=NOW,
    )
    assert out.context.subject_ref == "ENGLISH"
    assert out.context.component_ref is None
    assert out.context.grade is None
    assert out.context.class_id is None
    assert out.context.lesson_id is None


def test_component_change_keeps_subject_and_invalidates_descendants():
    out = apply_runtime_context_change(
        current=populated(),
        field="component_ref",
        value="GEOMETRY",
        source_page="standardization",
        source_control="component",
        occurred_at=NOW,
    )
    assert out.context.subject_ref == "MATH"
    assert out.context.component_ref == "GEOMETRY"
    assert out.context.grade is None
    assert out.context.class_id is None


def test_grade_change_invalidates_class_and_operational_context():
    out = apply_runtime_context_change(
        current=populated(),
        field="grade",
        value=7,
        source_page="standardization",
        source_control="grade",
        occurred_at=NOW,
    )
    assert out.context.grade == 7
    assert out.context.class_id is None
    assert out.context.timetable_slot_id is None


def test_class_change_invalidates_only_downstream_operational_fields():
    out = apply_runtime_context_change(
        current=populated(),
        field="class_id",
        value="6A2",
        source_page="ai",
        source_control="schedule_row",
        occurred_at=NOW,
    )
    assert out.context.subject_ref == "MATH"
    assert out.context.component_ref == "ALGEBRA"
    assert out.context.grade == 6
    assert out.context.class_id == "6A2"
    assert out.context.timetable_slot_id is None
    assert out.context.lesson_id is None


def test_bundle_republishes_valid_descendants_in_dependency_order():
    out = apply_runtime_context_bundle(
        current=populated(),
        values={
            "subject_ref": "ENGLISH",
            "component_ref": "LANGUAGE",
            "grade": 7,
            "class_id": "7A1",
        },
        source_page="ai",
        source_control="assignment_schedule",
        occurred_at=NOW,
    )
    assert out.context.subject_ref == "ENGLISH"
    assert out.context.component_ref == "LANGUAGE"
    assert out.context.grade == 7
    assert out.context.class_id == "7A1"
    assert out.context.lesson_id is None


def test_rejects_non_runtime_field():
    with pytest.raises(ValueError, match="UNSUPPORTED_RUNTIME_CONTEXT_FIELD"):
        apply_runtime_context_change(
            current=populated(),
            field="week_number",
            value=3,
            source_page="x",
            source_control="x",
            occurred_at=NOW,
        )
