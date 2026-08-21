import pytest

from lesson_planning_v2.weekly_lesson_plan_docx_layout import (
    WeeklyLessonPlanDocxLayoutProfile,
)


def test_default_profile_uses_times_new_roman_14():
    profile = WeeklyLessonPlanDocxLayoutProfile.default()

    assert profile.body_font == "Times New Roman"
    assert profile.body_size == 14


def test_default_page_margins_are_defined():
    profile = WeeklyLessonPlanDocxLayoutProfile.default()

    assert profile.top_margin_cm > 0
    assert profile.bottom_margin_cm > 0
    assert profile.left_margin_cm > 0
    assert profile.right_margin_cm > 0


def test_default_title_and_heading_sizes_are_not_smaller_than_body():
    profile = WeeklyLessonPlanDocxLayoutProfile.default()

    assert profile.title_size >= profile.body_size
    assert profile.heading_size >= profile.body_size


def test_default_line_spacing_is_positive():
    profile = WeeklyLessonPlanDocxLayoutProfile.default()

    assert profile.line_spacing > 0


def test_default_paragraph_spacing_is_non_negative():
    profile = WeeklyLessonPlanDocxLayoutProfile.default()

    assert profile.space_before_pt >= 0
    assert profile.space_after_pt >= 0


def test_layout_profile_can_override_font_and_size():
    profile = WeeklyLessonPlanDocxLayoutProfile(
        body_font="Arial",
        body_size=13,
        title_size=16,
        heading_size=14,
        top_margin_cm=2.0,
        bottom_margin_cm=2.0,
        left_margin_cm=3.0,
        right_margin_cm=2.0,
        line_spacing=1.15,
        space_before_pt=0,
        space_after_pt=6,
        header_alignment="center",
        approval_alignment="right",
    )

    assert profile.body_font == "Arial"
    assert profile.body_size == 13


@pytest.mark.parametrize(
    "field_name",
    (
        "body_font",
        "header_alignment",
        "approval_alignment",
    ),
)
def test_required_text_fields_cannot_be_blank(
    field_name,
):
    values = {
        "body_font": "Times New Roman",
        "body_size": 14,
        "title_size": 16,
        "heading_size": 14,
        "top_margin_cm": 2.0,
        "bottom_margin_cm": 2.0,
        "left_margin_cm": 3.0,
        "right_margin_cm": 2.0,
        "line_spacing": 1.15,
        "space_before_pt": 0,
        "space_after_pt": 6,
        "header_alignment": "center",
        "approval_alignment": "right",
    }

    values[field_name] = "   "

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        WeeklyLessonPlanDocxLayoutProfile(
            **values
        )


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
    ),
    (
        ("body_size", 0),
        ("title_size", 0),
        ("heading_size", 0),
        ("top_margin_cm", 0),
        ("bottom_margin_cm", 0),
        ("left_margin_cm", 0),
        ("right_margin_cm", 0),
        ("line_spacing", 0),
    ),
)
def test_positive_numeric_fields_are_validated(
    field_name,
    invalid_value,
):
    values = {
        "body_font": "Times New Roman",
        "body_size": 14,
        "title_size": 16,
        "heading_size": 14,
        "top_margin_cm": 2.0,
        "bottom_margin_cm": 2.0,
        "left_margin_cm": 3.0,
        "right_margin_cm": 2.0,
        "line_spacing": 1.15,
        "space_before_pt": 0,
        "space_after_pt": 6,
        "header_alignment": "center",
        "approval_alignment": "right",
    }

    values[field_name] = invalid_value

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        WeeklyLessonPlanDocxLayoutProfile(
            **values
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "space_before_pt",
        "space_after_pt",
    ),
)
def test_spacing_fields_cannot_be_negative(
    field_name,
):
    values = {
        "body_font": "Times New Roman",
        "body_size": 14,
        "title_size": 16,
        "heading_size": 14,
        "top_margin_cm": 2.0,
        "bottom_margin_cm": 2.0,
        "left_margin_cm": 3.0,
        "right_margin_cm": 2.0,
        "line_spacing": 1.15,
        "space_before_pt": 0,
        "space_after_pt": 6,
        "header_alignment": "center",
        "approval_alignment": "right",
    }

    values[field_name] = -1

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        WeeklyLessonPlanDocxLayoutProfile(
            **values
        )


@pytest.mark.parametrize(
    "alignment",
    (
        "left",
        "center",
        "right",
        "justify",
    ),
)
def test_supported_alignment_values_are_accepted(
    alignment,
):
    profile = WeeklyLessonPlanDocxLayoutProfile(
        body_font="Times New Roman",
        body_size=14,
        title_size=16,
        heading_size=14,
        top_margin_cm=2.0,
        bottom_margin_cm=2.0,
        left_margin_cm=3.0,
        right_margin_cm=2.0,
        line_spacing=1.15,
        space_before_pt=0,
        space_after_pt=6,
        header_alignment=alignment,
        approval_alignment=alignment,
    )

    assert profile.header_alignment == alignment
    assert profile.approval_alignment == alignment


def test_unsupported_alignment_is_rejected():
    with pytest.raises(
        ValueError,
        match="header_alignment",
    ):
        WeeklyLessonPlanDocxLayoutProfile(
            body_font="Times New Roman",
            body_size=14,
            title_size=16,
            heading_size=14,
            top_margin_cm=2.0,
            bottom_margin_cm=2.0,
            left_margin_cm=3.0,
            right_margin_cm=2.0,
            line_spacing=1.15,
            space_before_pt=0,
            space_after_pt=6,
            header_alignment="diagonal",
            approval_alignment="right",
        )
