import inspect

from lesson_planning_v2.services.weekly_lesson_plan_docx_renderer import (
    WeeklyLessonPlanDocxRenderer,
)
from lesson_planning_v2.services.weekly_lesson_plan_word_document_mapper import (
    WeeklyLessonPlanWordDocumentMapper,
)


def test_renderer_accepts_presentation_profile():
    signature = inspect.signature(
        WeeklyLessonPlanDocxRenderer.render
    )

    assert (
        "presentation_profile"
        in signature.parameters
    )


def test_renderer_does_not_accept_display_context():
    signature = inspect.signature(
        WeeklyLessonPlanDocxRenderer.render
    )

    assert (
        "display"
        not in signature.parameters
    )


def test_mapper_exposes_display_aware_mapping_contract():
    methods = {
        name
        for name, value in inspect.getmembers(
            WeeklyLessonPlanWordDocumentMapper,
            predicate=inspect.isfunction,
        )
        if not name.startswith("_")
    }

    assert (
        "map_with_display"
        in methods
    )


def test_map_with_display_accepts_display_context():
    signature = inspect.signature(
        WeeklyLessonPlanWordDocumentMapper
        .map_with_display
    )

    assert (
        "display"
        in signature.parameters
    )


def test_renderer_does_not_own_name_inference():
    source = inspect.getsource(
        WeeklyLessonPlanDocxRenderer
    )

    forbidden = (
        "GV002",
        "FOREIGN-LANGUAGE-1",
        "CLASS-6A1",
        "COMP-A",
    )

    for value in forbidden:
        assert value not in source


def test_mapper_does_not_own_name_inference():
    source = inspect.getsource(
        WeeklyLessonPlanWordDocumentMapper
    )

    forbidden = (
        "GV002",
        "FOREIGN-LANGUAGE-1",
        "CLASS-6A1",
        "COMP-A",
    )

    for value in forbidden:
        assert value not in source
