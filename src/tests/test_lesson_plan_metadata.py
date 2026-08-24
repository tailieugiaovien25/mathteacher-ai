from datetime import date

import pytest

from document_standardization.lesson_plan_metadata import (
    LessonPlanMetadata,
)


def test_empty_metadata_is_safe_noop():
    metadata = LessonPlanMetadata()

    assert metadata.is_empty is True
    assert metadata.overlay_values() == {}
    assert metadata.display_values() == {}


def test_metadata_normalizes_strings():
    metadata = LessonPlanMetadata(
        school_name="  THCS Chà Tở  ",
        teacher_name="  Nguyễn Văn A  ",
        subject_name="  Toán  ",
        class_name="  6A1  ",
        lesson_title="  Phân số  ",
    )

    assert (
        metadata.school_name
        == "THCS Chà Tở"
    )
    assert (
        metadata.teacher_name
        == "Nguyễn Văn A"
    )
    assert metadata.subject_name == "Toán"
    assert metadata.class_name == "6A1"
    assert (
        metadata.lesson_title
        == "Phân số"
    )


def test_blank_strings_become_none():
    metadata = LessonPlanMetadata(
        school_name="   ",
        teacher_name="",
        class_name="\t",
    )

    assert metadata.school_name is None
    assert metadata.teacher_name is None
    assert metadata.class_name is None

    assert metadata.is_empty is True
    assert metadata.overlay_values() == {}


def test_overlay_contains_only_supplied_values():
    metadata = LessonPlanMetadata(
        class_name="6A2",
        curriculum_period=12,
        teaching_date=date(
            2026,
            9,
            15,
        ),
    )

    assert metadata.overlay_values() == {
        "class_name": "6A2",
        "curriculum_period": 12,
        "teaching_date": date(
            2026,
            9,
            15,
        ),
    }


def test_display_values_formats_dates():
    metadata = LessonPlanMetadata(
        drafting_date=date(
            2026,
            9,
            13,
        ),
        teaching_date=date(
            2026,
            9,
            15,
        ),
    )

    assert metadata.display_values() == {
        "drafting_date":
            "13/09/2026",
        "teaching_date":
            "15/09/2026",
    }


@pytest.mark.parametrize(
    "value",
    (
        0,
        -1,
        True,
        1.5,
        "12",
    ),
)
def test_invalid_curriculum_period_rejected(
    value,
):
    with pytest.raises(
        (TypeError, ValueError),
    ):
        LessonPlanMetadata(
            curriculum_period=value,
        )


def test_invalid_date_rejected():
    with pytest.raises(TypeError):
        LessonPlanMetadata(
            teaching_date="15/09/2026",
        )


def test_model_is_immutable():
    metadata = LessonPlanMetadata(
        class_name="6A1",
    )

    with pytest.raises(
        AttributeError,
    ):
        metadata.class_name = "6A2"
