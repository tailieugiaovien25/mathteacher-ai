# V57-B PHASE 1
from datetime import date, datetime

import pytest

from portal_v2.context import (
    ContextChange,
    ContextFieldKind,
    ContextSynchronizationService,
    SystemContext,
    build_default_context_registry,
)


def test_registry_has_locked_authority_chain_fields() -> None:
    registry = build_default_context_registry()
    assert registry.get("subject_ref").authority == "TEACHING_ASSIGNMENT"
    assert registry.get("class_id").authority == "ACTIVE_TEACHER_TIMETABLE"
    assert registry.get("teaching_date").kind is ContextFieldKind.DERIVED
    assert registry.get("teaching_date").authority == "ACTIVE_TEACHER_TIMETABLE"
    assert registry.get("curriculum_period").authority == "PPCT_CURRICULUM"
    assert registry.get("lesson_id").authority == "PPCT_CURRICULUM"


def test_week_change_invalidates_downstream_context_without_fabrication() -> None:
    service = ContextSynchronizationService()
    current = SystemContext(
        user_id="U1", teacher_id="T1", academic_year="2026-2027",
        week_number=1, subject_ref="ENGLISH", component_ref="ENGLISH",
        grade=6, class_id="6A1", timetable_slot_id="SLOT-1",
        teaching_date=date(2026, 9, 7), timetable_period=1,
        curriculum_period=1, lesson_id="LESSON-1",
    )

    result = service.apply_change(
        current=current,
        change=ContextChange(
            field="week_number", value=2,
            source_page="weekly_schedule",
            source_control="week_selector",
            occurred_at=datetime(2026, 8, 29, 13, 0, 0),
        ),
    )

    assert result.context.week_number == 2
    assert result.context.subject_ref is None
    assert result.context.class_id is None
    assert result.context.timetable_slot_id is None
    assert result.context.teaching_date is None
    assert result.context.curriculum_period is None
    assert result.context.lesson_id is None
    assert result.context.context_version == 1


def test_subject_change_clears_stale_downstream_context() -> None:
    service = ContextSynchronizationService()
    current = SystemContext(
        user_id="U1", teacher_id="T1", academic_year="2026-2027",
        week_number=5, subject_ref="MATH", component_ref="ALGEBRA",
        grade=8, class_id="8A2", timetable_slot_id="SLOT-MATH",
        curriculum_period=7, lesson_id="MATH-7",
    )

    result = service.apply_value(
        current=current,
        field="subject_ref",
        value="ENGLISH",
        source_page="lesson_authoring",
        source_control="subject_selector",
    )

    assert result.context.subject_ref == "ENGLISH"
    assert result.context.component_ref is None
    assert result.context.grade is None
    assert result.context.class_id is None
    assert result.context.curriculum_period is None
    assert result.context.lesson_id is None


def test_same_value_is_noop() -> None:
    service = ContextSynchronizationService()
    current = SystemContext(week_number=5, context_version=8)
    result = service.apply_value(
        current=current, field="week_number", value=5,
        source_page="weekly_schedule", source_control="week_selector",
    )
    assert result.context is current
    assert result.events == ()
    assert result.context.context_version == 8


def test_unregistered_context_field_is_rejected() -> None:
    service = ContextSynchronizationService()
    with pytest.raises(KeyError, match="UNREGISTERED_CONTEXT_FIELD"):
        service.apply_value(
            current=SystemContext(),
            field="random_dropdown",
            value="X",
            source_page="any",
            source_control="any",
        )
