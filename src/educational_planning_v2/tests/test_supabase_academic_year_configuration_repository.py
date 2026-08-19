from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from educational_planning_v2.adapters.supabase_academic_year_configuration_repository import (
    SupabaseAcademicYearConfigurationRepository,
)
from educational_planning_v2.models.academic_year_configuration import (
    AcademicYearConfiguration,
    AcademicYearStatus,
)


class FakeResponse:
    def __init__(
        self,
        data: Any,
    ) -> None:
        self.data = data


class FakeQuery:
    def __init__(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        self._rows = rows
        self._filters: list[
            tuple[str, Any]
        ] = []
        self._limit = None

    def select(
        self,
        columns: str,
    ) -> "FakeQuery":
        return self

    def eq(
        self,
        column: str,
        value: Any,
    ) -> "FakeQuery":
        self._filters.append(
            (
                column,
                value,
            )
        )
        return self

    def limit(
        self,
        value: int,
    ) -> "FakeQuery":
        self._limit = value
        return self

    def order(
        self,
        column: str,
        *,
        desc: bool = False,
    ) -> "FakeQuery":
        return self

    def upsert(
        self,
        payload: dict[str, Any],
        *,
        on_conflict: str,
    ) -> "FakeQuery":
        existing = None

        for row in self._rows:
            if (
                row.get(on_conflict)
                == payload[on_conflict]
            ):
                existing = row
                break

        if existing is None:
            self._rows.append(
                dict(payload)
            )
        else:
            existing.update(
                payload
            )

        self._filters = [
            (
                on_conflict,
                payload[on_conflict],
            )
        ]

        return self

    def execute(
        self,
    ) -> FakeResponse:
        rows = list(
            self._rows
        )

        for column, value in self._filters:
            rows = [
                row
                for row in rows
                if row.get(column) == value
            ]

        if self._limit is not None:
            rows = rows[
                : self._limit
            ]

        return FakeResponse(
            rows
        )


class FakeClient:
    def __init__(
        self,
        rows: list[dict[str, Any]],
    ) -> None:
        self.rows = rows

    def table(
        self,
        name: str,
    ) -> FakeQuery:
        assert (
            name
            == "academic_year_configurations"
        )

        return FakeQuery(
            self.rows
        )


def make_configuration(
    *,
    academic_year_id="AY-2026-2027",
    academic_year="2026-2027",
    status=AcademicYearStatus.ACTIVE,
    is_current=False,
):
    return AcademicYearConfiguration(
        academic_year_id=academic_year_id,
        academic_year=academic_year,
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


def test_save_and_get_configuration():
    repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=FakeClient(
                rows=[],
            ),
        )
    )

    saved = repository.save(
        configuration=(
            make_configuration()
        )
    )

    loaded = repository.get(
        academic_year_id=(
            "AY-2026-2027"
        ),
    )

    assert saved == loaded
    assert loaded is not None
    assert (
        loaded.academic_year
        == "2026-2027"
    )


def test_get_current_returns_current_configuration():
    client = FakeClient(
        rows=[
            {
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "academic_year": (
                    "2026-2027"
                ),
                "start_date": (
                    "2026-08-24"
                ),
                "end_date": (
                    "2027-05-31"
                ),
                "opening_ceremony_date": (
                    "2026-09-05"
                ),
                "semester_1_start": (
                    "2026-08-24"
                ),
                "semester_1_end": (
                    "2027-01-17"
                ),
                "semester_2_start": (
                    "2027-01-18"
                ),
                "semester_2_end": (
                    "2027-05-31"
                ),
                "status": "ACTIVE",
                "is_current": True,
            },
        ],
    )

    repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=client,
        )
    )

    current = (
        repository.get_current()
    )

    assert current is not None
    assert current.is_current is True
    assert (
        current.academic_year
        == "2026-2027"
    )


def test_list_configurations_returns_models():
    client = FakeClient(
        rows=[
            {
                "academic_year_id": (
                    "AY-2026-2027"
                ),
                "academic_year": (
                    "2026-2027"
                ),
                "start_date": (
                    "2026-08-24"
                ),
                "end_date": (
                    "2027-05-31"
                ),
                "opening_ceremony_date": (
                    "2026-09-05"
                ),
                "semester_1_start": (
                    "2026-08-24"
                ),
                "semester_1_end": (
                    "2027-01-17"
                ),
                "semester_2_start": (
                    "2027-01-18"
                ),
                "semester_2_end": (
                    "2027-05-31"
                ),
                "status": "ACTIVE",
                "is_current": False,
            },
        ],
    )

    repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=client,
        )
    )

    result = (
        repository.list_configurations()
    )

    assert len(result) == 1
    assert (
        result[0].academic_year
        == "2026-2027"
    )


def test_set_current_activates_target_and_clears_previous():
    rows = [
        {
            "academic_year_id": (
                "AY-2025-2026"
            ),
            "academic_year": (
                "2025-2026"
            ),
            "start_date": (
                "2025-08-25"
            ),
            "end_date": (
                "2026-05-31"
            ),
            "opening_ceremony_date": (
                "2025-09-05"
            ),
            "semester_1_start": (
                "2025-08-25"
            ),
            "semester_1_end": (
                "2026-01-18"
            ),
            "semester_2_start": (
                "2026-01-19"
            ),
            "semester_2_end": (
                "2026-05-31"
            ),
            "status": "ACTIVE",
            "is_current": True,
        },
        {
            "academic_year_id": (
                "AY-2026-2027"
            ),
            "academic_year": (
                "2026-2027"
            ),
            "start_date": (
                "2026-08-24"
            ),
            "end_date": (
                "2027-05-31"
            ),
            "opening_ceremony_date": (
                "2026-09-05"
            ),
            "semester_1_start": (
                "2026-08-24"
            ),
            "semester_1_end": (
                "2027-01-17"
            ),
            "semester_2_start": (
                "2027-01-18"
            ),
            "semester_2_end": (
                "2027-05-31"
            ),
            "status": "ACTIVE",
            "is_current": False,
        },
    ]

    repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=FakeClient(
                rows=rows,
            ),
        )
    )

    current = repository.set_current(
        academic_year_id=(
            "AY-2026-2027"
        ),
    )

    assert current.is_current is True

    previous = repository.get(
        academic_year_id=(
            "AY-2025-2026"
        ),
    )

    assert previous is not None
    assert previous.is_current is False


def test_set_current_rejects_non_active_configuration():
    repository = (
        SupabaseAcademicYearConfigurationRepository(
            client=FakeClient(
                rows=[],
            ),
        )
    )

    repository.save(
        configuration=(
            make_configuration(
                status=(
                    AcademicYearStatus.DRAFT
                ),
                is_current=False,
            )
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "current academic year "
            "must be ACTIVE"
        ),
    ):
        repository.set_current(
            academic_year_id=(
                "AY-2026-2027"
            ),
        )


def test_repository_requires_client():
    with pytest.raises(
        ValueError,
        match=(
            "client must not be None"
        ),
    ):
        SupabaseAcademicYearConfigurationRepository(
            client=None,
        )
