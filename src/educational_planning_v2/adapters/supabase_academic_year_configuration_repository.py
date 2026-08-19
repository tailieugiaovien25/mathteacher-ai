from __future__ import annotations

from datetime import date
from typing import Any

from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
    AcademicYearStatus,
)
from educational_planning_v2.repositories.academic_year_configuration_repository import (
    AcademicYearConfigurationRepository,
)


class SupabaseAcademicYearConfigurationRepository(
    AcademicYearConfigurationRepository
):
    TABLE_NAME = "academic_year_configurations"

    def __init__(
        self,
        *,
        client: Any,
    ) -> None:
        if client is None:
            raise ValueError(
                "client must not be None"
            )

        self._client = client

    def save(
        self,
        *,
        configuration: AcademicYearConfiguration,
    ) -> AcademicYearConfiguration:
        if not isinstance(
            configuration,
            AcademicYearConfiguration,
        ):
            raise TypeError(
                "configuration must be "
                "AcademicYearConfiguration"
            )

        payload = {
            "academic_year_id": (
                configuration.academic_year_id
            ),
            "academic_year": (
                configuration.academic_year
            ),
            "start_date": (
                configuration.start_date.isoformat()
            ),
            "end_date": (
                configuration.end_date.isoformat()
            ),
            "opening_ceremony_date": (
                configuration.opening_ceremony_date.isoformat()
            ),
            "semester_1_start": (
                configuration.semester_1_start.isoformat()
            ),
            "semester_1_end": (
                configuration.semester_1_end.isoformat()
            ),
            "semester_2_start": (
                configuration.semester_2_start.isoformat()
            ),
            "semester_2_end": (
                configuration.semester_2_end.isoformat()
            ),
            "status": (
                configuration.status.value
            ),
            "is_current": (
                configuration.is_current
            ),
        }

        response = (
            self._client
            .table(self.TABLE_NAME)
            .upsert(
                payload,
                on_conflict="academic_year_id",
            )
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return configuration

        return self._from_row(
            rows[0]
        )

    def get(
        self,
        *,
        academic_year_id: str,
    ) -> AcademicYearConfiguration | None:
        normalized_id = self._required_text(
            academic_year_id,
            "academic_year_id",
        )

        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "academic_year_id",
                normalized_id,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    def get_current(
        self,
    ) -> AcademicYearConfiguration | None:
        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .eq(
                "is_current",
                True,
            )
            .limit(1)
            .execute()
        )

        rows = self._response_rows(
            response
        )

        if not rows:
            return None

        return self._from_row(
            rows[0]
        )

    def list_configurations(
        self,
    ) -> tuple[
        AcademicYearConfiguration,
        ...,
    ]:
        response = (
            self._client
            .table(self.TABLE_NAME)
            .select("*")
            .order(
                "academic_year",
                desc=True,
            )
            .execute()
        )

        return tuple(
            self._from_row(row)
            for row in self._response_rows(
                response
            )
        )

    def set_current(
        self,
        *,
        academic_year_id: str,
    ) -> AcademicYearConfiguration:
        normalized_id = self._required_text(
            academic_year_id,
            "academic_year_id",
        )

        current = self.get(
            academic_year_id=normalized_id,
        )

        if current is None:
            raise ValueError(
                "academic year configuration "
                "not found"
            )

        if (
            current.status
            is not AcademicYearStatus.ACTIVE
        ):
            raise ValueError(
                "current academic year "
                "must be ACTIVE"
            )

        existing = (
            self.list_configurations()
        )

        for item in existing:
            if (
                item.is_current
                and item.academic_year_id
                != normalized_id
            ):
                self.save(
                    configuration=(
                        AcademicYearConfiguration(
                            academic_year_id=(
                                item.academic_year_id
                            ),
                            academic_year=(
                                item.academic_year
                            ),
                            start_date=(
                                item.start_date
                            ),
                            end_date=(
                                item.end_date
                            ),
                            opening_ceremony_date=(
                                item.opening_ceremony_date
                            ),
                            semester_1_start=(
                                item.semester_1_start
                            ),
                            semester_1_end=(
                                item.semester_1_end
                            ),
                            semester_2_start=(
                                item.semester_2_start
                            ),
                            semester_2_end=(
                                item.semester_2_end
                            ),
                            status=(
                                item.status
                            ),
                            is_current=False,
                        )
                    )
                )

        updated = (
            AcademicYearConfiguration(
                academic_year_id=(
                    current.academic_year_id
                ),
                academic_year=(
                    current.academic_year
                ),
                start_date=(
                    current.start_date
                ),
                end_date=(
                    current.end_date
                ),
                opening_ceremony_date=(
                    current.opening_ceremony_date
                ),
                semester_1_start=(
                    current.semester_1_start
                ),
                semester_1_end=(
                    current.semester_1_end
                ),
                semester_2_start=(
                    current.semester_2_start
                ),
                semester_2_end=(
                    current.semester_2_end
                ),
                status=(
                    current.status
                ),
                is_current=True,
            )
        )

        return self.save(
            configuration=updated,
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> AcademicYearConfiguration:
        return AcademicYearConfiguration(
            academic_year_id=str(
                row["academic_year_id"]
            ),
            academic_year=str(
                row["academic_year"]
            ),
            start_date=date.fromisoformat(
                str(
                    row["start_date"]
                )
            ),
            end_date=date.fromisoformat(
                str(
                    row["end_date"]
                )
            ),
            opening_ceremony_date=date.fromisoformat(
                str(
                    row[
                        "opening_ceremony_date"
                    ]
                )
            ),
            semester_1_start=date.fromisoformat(
                str(
                    row["semester_1_start"]
                )
            ),
            semester_1_end=date.fromisoformat(
                str(
                    row["semester_1_end"]
                )
            ),
            semester_2_start=date.fromisoformat(
                str(
                    row["semester_2_start"]
                )
            ),
            semester_2_end=date.fromisoformat(
                str(
                    row["semester_2_end"]
                )
            ),
            status=AcademicYearStatus(
                str(
                    row["status"]
                )
            ),
            is_current=bool(
                row["is_current"]
            ),
        )

    @staticmethod
    def _required_text(
        value: str,
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
    def _response_rows(
        response: Any,
    ) -> list[dict[str, Any]]:
        data = getattr(
            response,
            "data",
            None,
        )

        if data is None:
            return []

        if not isinstance(
            data,
            list,
        ):
            raise TypeError(
                "Supabase response data must be a list"
            )

        if not all(
            isinstance(
                row,
                dict,
            )
            for row in data
        ):
            raise TypeError(
                "Supabase response rows must be dict"
            )

        return data
