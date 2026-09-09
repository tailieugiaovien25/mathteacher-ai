from pathlib import Path
from unittest.mock import patch

import pytest

from educational_planning_v2.models import TeachingSession
from document_standardization.lesson_plan_canonical_field_repair_runtime import (
    build_repair_scheduled_context,
    repair_canonical_field_bytes,
)


def _group_context():
    return {
        "subject_ref": "SUBJECT-ENGLISH",
        "component_ref": "FOREIGN_LANGUAGE_1",
        "lesson_id": "LESSON-10",
        "lesson_title": "Unit 2",
        "occurrences": [
            {
                "class_id": "6A1",
                "class_display": "6A1",
                "teaching_date": "2026-09-08",
                "timetable_period": 2,
                "curriculum_period": 10,
                "session": "MORNING",
                "period_in_lesson": 1,
            },
            {
                "class_id": "6A2",
                "class_display": "6A2",
                "teaching_date": "2026-09-09",
                "timetable_period": 3,
                "curriculum_period": 10,
                "session": "AFTERNOON",
                "period_in_lesson": 1,
            },
        ],
    }


def test_context_uses_first_canonical_occurrence_for_multiclass():
    context = build_repair_scheduled_context(
        _group_context(),
        field_key="lesson_title",
        teacher_value="Unit 2",
    )
    assert context.class_id == "6A1"
    assert context.teaching_date.isoformat() == "2026-09-08"
    assert context.curriculum_period == 10
    assert context.session is TeachingSession.MORNING
    assert context.period_in_lesson == 1


def test_teaching_date_uses_teacher_confirmed_value():
    context = build_repair_scheduled_context(
        _group_context(),
        field_key="teaching_date",
        teacher_value="10/09/2026",
    )
    assert context.teaching_date.isoformat() == "2026-09-10"
    assert context.class_id == "6A1"


def test_missing_repair_contract_fails_closed():
    group_context = _group_context()
    group_context["occurrences"][0].pop("session")
    with pytest.raises(ValueError, match="session"):
        build_repair_scheduled_context(
            group_context,
            field_key="class_name",
            teacher_value="6A1",
        )


def test_class_name_maps_to_class_id_and_bytes_use_temporary_files():
    def fake_repair(source, output, *, field_name, value, context):
        assert isinstance(source, Path)
        assert isinstance(output, Path)
        assert source.read_bytes() == b"source-docx"
        assert field_name == "class_id"
        assert value == "6A1"
        assert context.class_id == "6A1"
        output.write_bytes(b"repaired-docx")
        return True

    target = (
        "document_standardization.lesson_plan_canonical_field_repair_runtime."
        "repair_lesson_plan_canonical_field"
    )
    with patch(target, side_effect=fake_repair):
        result = repair_canonical_field_bytes(
            b"source-docx",
            group_context=_group_context(),
            field_key="class_name",
            teacher_value="6A1",
        )

    assert result.changed is True
    assert result.content == b"repaired-docx"
    assert result.repair_field_name == "class_id"
