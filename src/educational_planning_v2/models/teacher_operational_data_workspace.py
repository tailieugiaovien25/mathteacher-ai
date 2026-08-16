from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataType,
)


@dataclass(frozen=True)
class TeacherOperationalDataWorkspace:
    owner_id: str
    academic_year: str
    ppct_source: OperationalDataSource | None = None
    timetable_source: OperationalDataSource | None = None
    academic_week_source: OperationalDataSource | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "owner_id",
            self._required_text(
                self.owner_id,
                "owner_id",
            ),
        )

        object.__setattr__(
            self,
            "academic_year",
            self._required_text(
                self.academic_year,
                "academic_year",
            ),
        )

        self._validate_source(
            source=self.ppct_source,
            expected_type=OperationalDataType.PPCT,
            field_name="ppct_source",
        )

        self._validate_source(
            source=self.timetable_source,
            expected_type=OperationalDataType.TIMETABLE,
            field_name="timetable_source",
        )

        self._validate_source(
            source=self.academic_week_source,
            expected_type=OperationalDataType.ACADEMIC_WEEK,
            field_name="academic_week_source",
        )

    def source_for(
        self,
        data_type: OperationalDataType,
    ) -> OperationalDataSource | None:
        if not isinstance(
            data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        mapping = {
            OperationalDataType.PPCT: self.ppct_source,
            OperationalDataType.TIMETABLE: self.timetable_source,
            OperationalDataType.ACADEMIC_WEEK: self.academic_week_source,
        }

        if data_type not in mapping:
            raise ValueError(
                "data_type is not part of the teacher "
                "operational data workspace"
            )

        return mapping[data_type]

    def available_sources(
        self,
    ) -> tuple[OperationalDataSource, ...]:
        return tuple(
            source
            for source in (
                self.ppct_source,
                self.timetable_source,
                self.academic_week_source,
            )
            if source is not None
        )

    def _validate_source(
        self,
        *,
        source: OperationalDataSource | None,
        expected_type: OperationalDataType,
        field_name: str,
    ) -> None:
        if source is None:
            return

        if not isinstance(
            source,
            OperationalDataSource,
        ):
            raise TypeError(
                f"{field_name} must be "
                "OperationalDataSource or None"
            )

        if source.data_type is not expected_type:
            raise ValueError(
                f"{field_name} must reference "
                f"{expected_type.value}"
            )

        if source.owner_id != self.owner_id:
            raise ValueError(
                f"{field_name} owner does not match workspace"
            )

        if source.academic_year != self.academic_year:
            raise ValueError(
                f"{field_name} academic year does not "
                "match workspace"
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
