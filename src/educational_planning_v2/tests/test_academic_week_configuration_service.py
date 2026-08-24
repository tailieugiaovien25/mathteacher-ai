from datetime import date

from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
)
from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
    AcademicYearStatus,
)
from educational_planning_v2.services.academic_week_configuration_service import (
    AcademicWeekConfigurationService,
)


class FakeRepository:
    def __init__(self):
        self.items = {}

    def save(self, *, week):
        self.items[
            week.academic_week_id
        ] = week
        return week

    def list_weeks(
        self,
        *,
        academic_year_id,
    ):
        return tuple(
            item
            for item in self.items.values()
            if item.academic_year_id
            == academic_year_id
        )


def make_year():
    return AcademicYearConfiguration(
        academic_year_id=(
            "academic-year-2026-2027"
        ),
        academic_year="2026-2027",
        start_date=date(2026, 9, 7),
        end_date=date(2027, 5, 31),
        opening_ceremony_date=(
            date(2026, 9, 7)
        ),
        semester_1_start=(
            date(2026, 9, 7)
        ),
        semester_1_end=(
            date(2027, 1, 10)
        ),
        semester_2_start=(
            date(2027, 1, 11)
        ),
        semester_2_end=(
            date(2027, 5, 31)
        ),
        status=AcademicYearStatus.ACTIVE,
        is_current=True,
    )


def test_generates_40_weeks():
    repository = FakeRepository()

    service = (
        AcademicWeekConfigurationService(
            repository=repository
        )
    )

    weeks = service.ensure_weeks(
        academic_year=make_year()
    )

    assert len(weeks) == 40

    assert weeks[0].week_number == 1
    assert weeks[0].start_date == (
        date(2026, 9, 7)
    )
    assert weeks[0].end_date == (
        date(2026, 9, 13)
    )

    assert weeks[1].start_date == (
        date(2026, 9, 14)
    )


def test_manual_override_is_preserved():
    repository = FakeRepository()

    manual = AcademicWeekConfiguration(
        academic_week_id=(
            "academic-year-2026-2027-week-02"
        ),
        academic_year_id=(
            "academic-year-2026-2027"
        ),
        academic_year="2026-2027",
        week_number=2,
        start_date=date(2026, 9, 15),
        end_date=date(2026, 9, 21),
        is_manual_override=True,
        note="ADMIN adjusted",
    )

    repository.save(
        week=manual
    )

    service = (
        AcademicWeekConfigurationService(
            repository=repository
        )
    )

    weeks = service.ensure_weeks(
        academic_year=make_year()
    )

    week_2 = next(
        item
        for item in weeks
        if item.week_number == 2
    )

    assert week_2.start_date == (
        date(2026, 9, 15)
    )
    assert week_2.is_manual_override is True


def test_override_marks_week_manual():
    repository = FakeRepository()

    service = (
        AcademicWeekConfigurationService(
            repository=repository
        )
    )

    week = AcademicWeekConfiguration(
        academic_week_id="year-week-01",
        academic_year_id="year",
        academic_year="2026-2027",
        week_number=1,
        start_date=date(2026, 9, 7),
        end_date=date(2026, 9, 13),
    )

    saved = service.override_week(
        week=week
    )

    assert saved.is_manual_override is True
