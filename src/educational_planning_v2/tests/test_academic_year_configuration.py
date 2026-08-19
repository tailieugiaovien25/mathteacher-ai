from datetime import date

import pytest

from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
    AcademicYearStatus,
    normalize_academic_year,
)


def test_normalize_academic_year_removes_spaces():
    assert (
        normalize_academic_year(
            "2026 - 2027"
        )
        == "2026-2027"
    )


def test_normalize_academic_year_accepts_en_dash():
    assert (
        normalize_academic_year(
            "2026\u20132027"
        )
        == "2026-2027"
    )


def test_normalize_academic_year_rejects_invalid_range():
    with pytest.raises(
        ValueError,
        match=(
            "end year must equal "
            r"start year \+ 1"
        ),
    ):
        normalize_academic_year(
            "2026-2028"
        )


def make_configuration(
    *,
    status=AcademicYearStatus.ACTIVE,
    is_current=True,
):
    return AcademicYearConfiguration(
        academic_year_id=(
            "AY-2026-2027"
        ),
        academic_year=(
            "2026 - 2027"
        ),
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2027,
            5,
            31,
        ),
        opening_ceremony_date=date(
            2026,
            9,
            5,
        ),
        semester_1_start=date(
            2026,
            8,
            24,
        ),
        semester_1_end=date(
            2027,
            1,
            17,
        ),
        semester_2_start=date(
            2027,
            1,
            18,
        ),
        semester_2_end=date(
            2027,
            5,
            31,
        ),
        status=status,
        is_current=is_current,
    )


def test_configuration_normalizes_academic_year():
    configuration = (
        make_configuration()
    )

    assert (
        configuration.academic_year
        == "2026-2027"
    )


def test_current_academic_year_must_be_active():
    with pytest.raises(
        ValueError,
        match=(
            "current academic year "
            "must be ACTIVE"
        ),
    ):
        make_configuration(
            status=(
                AcademicYearStatus.DRAFT
            ),
            is_current=True,
        )


def test_opening_ceremony_must_be_inside_academic_year():
    with pytest.raises(
        ValueError,
        match=(
            "opening_ceremony_date must "
            "be inside academic year"
        ),
    ):
        AcademicYearConfiguration(
            academic_year_id=(
                "AY-2026-2027"
            ),
            academic_year=(
                "2026-2027"
            ),
            start_date=date(
                2026,
                8,
                24,
            ),
            end_date=date(
                2027,
                5,
                31,
            ),
            opening_ceremony_date=date(
                2026,
                8,
                1,
            ),
            semester_1_start=date(
                2026,
                8,
                24,
            ),
            semester_1_end=date(
                2027,
                1,
                17,
            ),
            semester_2_start=date(
                2027,
                1,
                18,
            ),
            semester_2_end=date(
                2027,
                5,
                31,
            ),
            status=(
                AcademicYearStatus.ACTIVE
            ),
            is_current=True,
        )
