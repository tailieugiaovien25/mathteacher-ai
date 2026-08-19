from datetime import date

import pytest

from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
)


def make_week(**changes):
    values = {
        "academic_week_id": "2026-2027-week-01",
        "academic_year_id": "academic-year-2026-2027",
        "academic_year": "2026-2027",
        "week_number": 1,
        "start_date": date(2026, 9, 7),
        "end_date": date(2026, 9, 13),
    }
    values.update(changes)
    return AcademicWeekConfiguration(**values)


def test_academic_week_configuration_is_valid():
    week = make_week()

    assert week.week_number == 1
    assert week.start_date == date(2026, 9, 7)


@pytest.mark.parametrize(
    "week_number",
    (0, 41),
)
def test_week_number_must_be_1_to_40(
    week_number,
):
    with pytest.raises(
        ValueError,
        match="between 1 and 40",
    ):
        make_week(
            week_number=week_number
        )


def test_start_date_must_not_be_after_end_date():
    with pytest.raises(
        ValueError,
        match="start_date",
    ):
        make_week(
            start_date=date(2026, 9, 14),
            end_date=date(2026, 9, 13),
        )
