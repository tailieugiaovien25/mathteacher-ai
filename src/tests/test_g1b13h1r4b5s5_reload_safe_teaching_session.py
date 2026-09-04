from datetime import date
from types import SimpleNamespace

import pytest

from document_standardization.lesson_plan_document_context_applier import (
    _g1b_rehydrate_scheduled_lesson_context,
    _g1b_rehydrate_teaching_session,
)
from educational_planning_v2.models import TeachingSession
from lesson_planning_v2.contexts import ScheduledLessonContext


def _stale_context_with_session(stale_session):
    stale_type = type(
        "ScheduledLessonContext",
        (),
        {"__module__": ScheduledLessonContext.__module__},
    )
    value = stale_type()
    payload = {
        "teaching_date": date(2026, 9, 2),
        "drafting_date": date(2026, 9, 1),
        "class_id": "6A1",
        "subject_ref": "ENGLISH",
        "component_ref": None,
        "curriculum_period": 1,
        "lesson_id": "LESSON-1",
        "lesson_title": "Lesson 1",
        "session": stale_session,
        "timetable_period": 1,
        "period_in_lesson": 1,
    }
    for key, item in payload.items():
        setattr(value, key, item)
    return value


def test_s5_rehydrates_stale_teaching_session_by_value():
    stale_session = SimpleNamespace(value="MORNING", name="MORNING")
    rebuilt = _g1b_rehydrate_scheduled_lesson_context(
        _stale_context_with_session(stale_session)
    )
    assert isinstance(rebuilt, ScheduledLessonContext)
    assert rebuilt.session is TeachingSession.MORNING


def test_s5_rehydrates_stale_teaching_session_by_name():
    stale_session = SimpleNamespace(value=None, name="AFTERNOON")
    rebuilt = _g1b_rehydrate_scheduled_lesson_context(
        _stale_context_with_session(stale_session)
    )
    assert rebuilt.session is TeachingSession.AFTERNOON


def test_s5_keeps_current_canonical_teaching_session():
    assert (
        _g1b_rehydrate_teaching_session(TeachingSession.MORNING)
        is TeachingSession.MORNING
    )


def test_s5_rejects_unrelated_invalid_session():
    with pytest.raises(TypeError, match="session must be TeachingSession"):
        _g1b_rehydrate_teaching_session(object())


def test_s5_still_rejects_unrelated_context_type():
    unrelated = SimpleNamespace(
        teaching_date=date(2026, 9, 2),
        drafting_date=date(2026, 9, 1),
        class_id="6A1",
        subject_ref="ENGLISH",
        component_ref=None,
        curriculum_period=1,
        lesson_id="LESSON-1",
        lesson_title="Lesson 1",
        session=TeachingSession.MORNING,
        timetable_period=1,
        period_in_lesson=1,
    )
    with pytest.raises(TypeError, match="context must be ScheduledLessonContext"):
        _g1b_rehydrate_scheduled_lesson_context(unrelated)
