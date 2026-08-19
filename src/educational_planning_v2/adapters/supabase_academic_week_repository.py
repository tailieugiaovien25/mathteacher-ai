from __future__ import annotations

from datetime import date
from typing import Any

from educational_planning_v2.models.academic_week_configuration import (
    AcademicWeekConfiguration,
    AcademicWeekStatus,
)
from educational_planning_v2.repositories.academic_week_repository import (
    AcademicWeekRepository,
)


class SupabaseAcademicWeekRepository(
    AcademicWeekRepository
):
    TABLE_NAME = "academic_weeks"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError("client must not be None")

        self._client = client

    def save(
        self,
        *,
        week: AcademicWeekConfiguration,
    ) -> AcademicWeekConfiguration:
        if not isinstance(
            week,
            AcademicWeekConfiguration,
        ):
            raise TypeError(
                "week must be AcademicWeekConfiguration"
            )

        payload = {
            "academic_week_id": week.academic_week_id,
            "academic_year_id": week.academic_year_id,
            "academic_year": week.academic_year,
            "week_number": week.week_number,
            "start_date": week.start_date.isoformat(),
            "end_date": week.end_date.isoformat(),
            "status": week.status.value,
            "is_manual_override": week.is_manual_override,
            "note": week.note,
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                payload,
                on_conflict="academic_week_id",
            )
            .execute()
        )

        rows = self._response_rows(response)

        if rows:
            return self._from_row(rows[0])

        verified = self.get(
            academic_week_id=week.academic_week_id
        )

        if verified is None:
            raise RuntimeError(
                "Supabase did not persist academic week "
                f"{week.academic_week_id!r}."
            )

        return verified

    def get(
        self,
        *,
        academic_week_id: str,
    ) -> AcademicWeekConfiguration | None:
        academic_week_id = self._required_text(
            academic_week_id,
            "academic_week_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "academic_week_id",
                academic_week_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(response)

        if not rows:
            return None

        return self._from_row(rows[0])

    def get_week(
        self,
        *,
        academic_year_id: str,
        week_number: int,
    ) -> AcademicWeekConfiguration | None:
        academic_year_id = self._required_text(
            academic_year_id,
            "academic_year_id",
        )

        self._week_number(week_number)

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "academic_year_id",
                academic_year_id,
            )
            .eq(
                "week_number",
                week_number,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(response)

        if not rows:
            return None

        return self._from_row(rows[0])

    def list_weeks(
        self,
        *,
        academic_year_id: str,
    ) -> tuple[AcademicWeekConfiguration, ...]:
        academic_year_id = self._required_text(
            academic_year_id,
            "academic_year_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "academic_year_id",
                academic_year_id,
            )
            .order("week_number")
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in self._response_rows(response)
        )

    def delete(
        self,
        *,
        academic_week_id: str,
    ) -> None:
        academic_week_id = self._required_text(
            academic_week_id,
            "academic_week_id",
        )

        (
            self._client
            .table(self.TABLE_NAME)
            .delete()
            .eq(
                "academic_week_id",
                academic_week_id,
            )
            .execute()
        )

        remaining = self.get(
            academic_week_id=academic_week_id
        )

        if remaining is not None:
            raise RuntimeError(
                "Supabase did not delete academic week "
                f"{academic_week_id!r}."
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> AcademicWeekConfiguration:
        return AcademicWeekConfiguration(
            academic_week_id=str(
                row["academic_week_id"]
            ),
            academic_year_id=str(
                row["academic_year_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            week_number=int(
                row["week_number"]
            ),
            start_date=date.fromisoformat(
                str(row["start_date"])
            ),
            end_date=date.fromisoformat(
                str(row["end_date"])
            ),
            status=AcademicWeekStatus(
                str(row["status"])
            ),
            is_manual_override=bool(
                row["is_manual_override"]
            ),
            note=(
                str(row["note"])
                if row.get("note") is not None
                else None
            ),
        )

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return value

    @staticmethod
    def _week_number(value: int) -> int:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 1 <= value <= 40
        ):
            raise ValueError(
                "week_number must be between 1 and 40"
            )

        return value

    @staticmethod
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(response, "data", None)

        if data is None:
            return []

        if not isinstance(data, list):
            raise TypeError(
                "Supabase response data must be a list"
            )

        if not all(
            isinstance(row, dict)
            for row in data
        ):
            raise TypeError(
                "Supabase response rows must be dict"
            )

        return data
