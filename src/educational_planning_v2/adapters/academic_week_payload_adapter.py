from __future__ import annotations

from datetime import date

from educational_planning_v2.models.operational_data_source import (
    OperationalDataType,
)
from educational_planning_v2.models.operational_payload import (
    OperationalPayloadEnvelope,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    AcademicWeek,
)


class AcademicWeekPayloadAdapter:
    """
    Convert an ACADEMIC_WEEK operational payload into canonical
    AcademicWeek domain objects.

    The adapter owns no persistence, Supabase, workbook, UI,
    or school-calendar rules.
    """

    def parse(
        self,
        *,
        envelope: OperationalPayloadEnvelope,
    ) -> tuple[AcademicWeek, ...]:
        if not isinstance(
            envelope,
            OperationalPayloadEnvelope,
        ):
            raise TypeError(
                "envelope must be OperationalPayloadEnvelope"
            )

        if (
            envelope.reference.data_type
            is not OperationalDataType.ACADEMIC_WEEK
        ):
            raise ValueError(
                "payload must have ACADEMIC_WEEK data type"
            )

        payload = envelope.payload

        if not isinstance(
            payload,
            (tuple, list),
        ):
            raise TypeError(
                "ACADEMIC_WEEK payload must be a sequence"
            )

        result = []

        for item in payload:
            if not isinstance(
                item,
                dict,
            ):
                raise TypeError(
                    "ACADEMIC_WEEK payload row must be dict"
                )

            result.append(
                AcademicWeek(
                    academic_year=(
                        self._required_text(
                            item.get(
                                "academic_year"
                            ),
                            "academic_year",
                        )
                    ),
                    week_number=(
                        self._positive_int(
                            item.get(
                                "week_number"
                            ),
                            "week_number",
                        )
                    ),
                    start_date=(
                        self._date_value(
                            item.get(
                                "start_date"
                            ),
                            "start_date",
                        )
                    ),
                    end_date=(
                        self._date_value(
                            item.get(
                                "end_date"
                            ),
                            "end_date",
                        )
                    ),
                )
            )

        self._validate_unique_weeks(
            tuple(result)
        )

        return tuple(
            sorted(
                result,
                key=lambda item: (
                    item.academic_year,
                    item.week_number,
                ),
            )
        )

    def find_week(
        self,
        *,
        envelope: OperationalPayloadEnvelope,
        academic_year: str,
        week_number: int,
    ) -> AcademicWeek:
        academic_year = self._required_text(
            academic_year,
            "academic_year",
        )

        week_number = self._positive_int(
            week_number,
            "week_number",
        )

        matches = tuple(
            week
            for week in self.parse(
                envelope=envelope
            )
            if (
                week.academic_year
                == academic_year
                and week.week_number
                == week_number
            )
        )

        if not matches:
            raise LookupError(
                "academic week not found: "
                f"{academic_year} week {week_number}"
            )

        if len(matches) > 1:
            raise ValueError(
                "multiple academic weeks found: "
                f"{academic_year} week {week_number}"
            )

        return matches[0]

    @staticmethod
    def _validate_unique_weeks(
        weeks: tuple[AcademicWeek, ...],
    ) -> None:
        seen = set()

        for week in weeks:
            key = (
                week.academic_year,
                week.week_number,
            )

            if key in seen:
                raise ValueError(
                    "duplicate academic week: "
                    f"{week.academic_year} "
                    f"week {week.week_number}"
                )

            seen.add(key)

    @staticmethod
    def _required_text(
        value,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized

    @staticmethod
    def _positive_int(
        value,
        field_name: str,
    ) -> int:
        if (
            not isinstance(
                value,
                int,
            )
            or isinstance(
                value,
                bool,
            )
            or value <= 0
        ):
            raise ValueError(
                f"{field_name} must be a positive integer"
            )

        return value

    @staticmethod
    def _date_value(
        value,
        field_name: str,
    ) -> date:
        if isinstance(
            value,
            date,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            try:
                return date.fromisoformat(
                    value.strip()
                )
            except ValueError as error:
                raise ValueError(
                    f"{field_name} must be ISO date"
                ) from error

        raise TypeError(
            f"{field_name} must be date or ISO date string"
        )
