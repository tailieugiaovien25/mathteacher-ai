import inspect

from docx import Document
from docx.shared import Pt

from lesson_planning_v2.services.weekly_lesson_plan_docx_renderer import (
    WeeklyLessonPlanDocxRenderer,
)
from lesson_planning_v2.weekly_lesson_plan_docx_layout import (
    WeeklyLessonPlanDocxLayoutProfile,
)


def test_renderer_accepts_layout_profile():
    signature = inspect.signature(
        WeeklyLessonPlanDocxRenderer.render
    )

    assert (
        "layout_profile"
        in signature.parameters
    )


def test_layout_profile_is_optional_for_backward_compatibility():
    signature = inspect.signature(
        WeeklyLessonPlanDocxRenderer.render
    )

    parameter = (
        signature.parameters[
            "layout_profile"
        ]
    )

    assert parameter.default is None


def test_renderer_source_does_not_hardcode_default_font():
    source = inspect.getsource(
        WeeklyLessonPlanDocxRenderer
    )

    assert (
        '"Times New Roman"'
        not in source
    )

    assert (
        "'Times New Roman'"
        not in source
    )


def test_default_layout_policy_is_times_new_roman_14():
    profile = (
        WeeklyLessonPlanDocxLayoutProfile
        .default()
    )

    assert (
        profile.body_font
        == "Times New Roman"
    )

    assert profile.body_size == 14


def test_docx_normal_style_can_be_configured_from_profile(
    tmp_path,
):
    output = (
        tmp_path
        / "layout-style.docx"
    )

    docx = Document()

    profile = (
        WeeklyLessonPlanDocxLayoutProfile
        .default()
    )

    style = docx.styles["Normal"]

    style.font.name = (
        profile.body_font
    )

    style.font.size = Pt(
        profile.body_size
    )

    docx.save(output)

    loaded = Document(output)

    normal = loaded.styles["Normal"]

    assert (
        normal.font.name
        == profile.body_font
    )

    assert (
        normal.font.size.pt
        == profile.body_size
    )


def test_default_layout_margins_have_expected_values():
    profile = (
        WeeklyLessonPlanDocxLayoutProfile
        .default()
    )

    assert profile.top_margin_cm == 2.0
    assert profile.bottom_margin_cm == 2.0
    assert profile.left_margin_cm == 3.0
    assert profile.right_margin_cm == 2.0
