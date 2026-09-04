from dataclasses import make_dataclass
from datetime import date
from pathlib import Path
from typing import get_type_hints

from document_standardization.lesson_plan_document_context_applier import (
    _g1b_rehydrate_scheduled_lesson_context,
)
from lesson_planning_v2.contexts.scheduled_lesson_context import ScheduledLessonContext


def _valid_payload():
    hints = get_type_hints(ScheduledLessonContext)
    session_type = hints["session"]
    session_value = next(iter(session_type))
    return {
        "teaching_date": date(2026, 9, 1),
        "drafting_date": date(2026, 8, 31),
        "class_id": "6A1",
        "subject_ref": "ENGLISH",
        "component_ref": None,
        "curriculum_period": 1,
        "lesson_id": "L1",
        "lesson_title": "Lesson 1",
        "session": session_value,
        "timetable_period": 1,
        "period_in_lesson": 1,
    }


def _stale_equivalent_type():
    fields = list(ScheduledLessonContext.__dataclass_fields__.keys())
    stale_type = make_dataclass(
        "ScheduledLessonContext",
        [(name, object) for name in fields],
        frozen=True,
    )
    stale_type.__module__ = ScheduledLessonContext.__module__
    return stale_type


def test_reload_equivalent_context_is_rehydrated():
    StaleContext = _stale_equivalent_type()
    payload = _valid_payload()
    stale = StaleContext(**payload)

    assert type(stale) is not ScheduledLessonContext
    assert type(stale).__module__ == ScheduledLessonContext.__module__
    assert type(stale).__name__ == ScheduledLessonContext.__name__

    current = _g1b_rehydrate_scheduled_lesson_context(stale)

    assert type(current) is ScheduledLessonContext
    for name, value in payload.items():
        assert getattr(current, name) == value


def test_unrelated_context_is_rejected():
    class WrongContext:
        pass

    try:
        _g1b_rehydrate_scheduled_lesson_context(WrongContext())
    except TypeError as error:
        assert "context must be ScheduledLessonContext" in str(error)
    else:
        raise AssertionError("WrongContext must be rejected")


def test_apply_uses_reload_safe_context_and_keeps_old_diagnostic_marker():
    root = Path(__file__).resolve().parents[2]
    source = root / "src/document_standardization/lesson_plan_document_context_applier.py"
    text = source.read_text(encoding="utf-8-sig")
    assert "G1B_13H1R4B5M_CONTEXT_IDENTITY_DIAGNOSTIC" not in text
    assert "G1B_13H1R4B5S4_REHYDRATE_STALE_CONTEXT" in text
    assert "G1B_13H1R4B5S4_APPLY_RELOAD_SAFE_CONTEXT" in text
    assert "context = _g1b_rehydrate_scheduled_lesson_context(context)" in text
