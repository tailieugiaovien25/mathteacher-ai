from __future__ import annotations

from datetime import timedelta

from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
    AcademicWeekStatus,
)
from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
)
from educational_planning_v2.repositories.academic_week_repository import (
    AcademicWeekRepository,
)


class AcademicWeekConfigurationService:
    WEEK_COUNT = 40

    def __init__(
        self,
        *,
        repository: AcademicWeekRepository,
    ) -> None:
        if repository is None:
            raise ValueError(
                "repository must not be None"
            )

        self._repository = repository

    def ensure_weeks(
        self,
        *,
        academic_year: AcademicYearConfiguration,
    ) -> tuple[AcademicWeekConfiguration, ...]:
        if not isinstance(
            academic_year,
            AcademicYearConfiguration,
        ):
            raise TypeError(
                "academic_year must be "
                "AcademicYearConfiguration"
            )

        existing = {
            item.week_number: item
            for item in self._repository.list_weeks(
                academic_year_id=(
                    academic_year.academic_year_id
                )
            )
        }

        result = []

        for week_number in range(
            1,
            self.WEEK_COUNT + 1,
        ):
            current = existing.get(
                week_number
            )

            # ADMIN manual adjustment is authoritative.
            if (
                current is not None
                and current.is_manual_override
            ):
                result.append(current)
                continue

            start_date = (
                academic_year.start_date
                + timedelta(
                    days=(week_number - 1) * 7
                )
            )

            end_date = (
                start_date
                + timedelta(days=6)
            )

            week = AcademicWeekConfiguration(
                academic_week_id=(
                    f"{academic_year.academic_year_id}"
                    f"-week-{week_number:02d}"
                ),
                academic_year_id=(
                    academic_year.academic_year_id
                ),
                academic_year=(
                    academic_year.academic_year
                ),
                week_number=week_number,
                start_date=start_date,
                end_date=end_date,
                status=AcademicWeekStatus.ACTIVE,
                is_manual_override=False,
                note=None,
            )

            saved = self._repository.save(
                week=week
            )

            result.append(saved)

        return tuple(result)

    def override_week(
        self,
        *,
        week: AcademicWeekConfiguration,
    ) -> AcademicWeekConfiguration:
        if not isinstance(
            week,
            AcademicWeekConfiguration,
        ):
            raise TypeError(
                "week must be "
                "AcademicWeekConfiguration"
            )

        manual_week = AcademicWeekConfiguration(
            academic_week_id=(
                week.academic_week_id
            ),
            academic_year_id=(
                week.academic_year_id
            ),
            academic_year=(
                week.academic_year
            ),
            week_number=(
                week.week_number
            ),
            start_date=(
                week.start_date
            ),
            end_date=(
                week.end_date
            ),
            status=week.status,
            is_manual_override=True,
            note=week.note,
        )

        return self._repository.save(
            week=manual_week
        )
