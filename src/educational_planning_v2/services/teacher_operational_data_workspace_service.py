from __future__ import annotations

from dataclasses import dataclass
import re

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.teacher_operational_data_workspace import (
    TeacherOperationalDataWorkspace,
)
from educational_planning_v2.repositories.operational_data_source_repository import (
    OperationalDataSourceRepository,
)


@dataclass(frozen=True)
class TeacherOperationalDataWorkspaceRequest:
    owner_id: str
    academic_year: str

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
            self._normalize_academic_year(
                self.academic_year,
            ),
        )

    @staticmethod
    def _normalize_academic_year(
        value: str,
    ) -> str:
        normalized = TeacherOperationalDataWorkspaceRequest._required_text(
            value,
            "academic_year",
        )

        match = re.fullmatch(
            r"(\d{4})\s*-\s*(\d{4})",
            normalized,
        )

        if match is None:
            return normalized

        return f"{match.group(1)}-{match.group(2)}"

    @staticmethod
    def _required_text(
        value: str,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise TypeError(
                f"{field_name} must be str"
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return normalized


class TeacherOperationalDataWorkspaceService:
    def __init__(
        self,
        repository: OperationalDataSourceRepository,
    ) -> None:
        if not isinstance(
            repository,
            OperationalDataSourceRepository,
        ):
            raise TypeError(
                "repository must implement "
                "OperationalDataSourceRepository"
            )

        self._repository = repository

    def build(
        self,
        *,
        request: TeacherOperationalDataWorkspaceRequest,
    ) -> TeacherOperationalDataWorkspace:
        if not isinstance(
            request,
            TeacherOperationalDataWorkspaceRequest,
        ):
            raise TypeError(
                "request must be "
                "TeacherOperationalDataWorkspaceRequest"
            )

        return TeacherOperationalDataWorkspace(
            owner_id=request.owner_id,
            academic_year=request.academic_year,
            ppct_source=self._single_active_source(
                owner_id=request.owner_id,
                academic_year=request.academic_year,
                data_type=OperationalDataType.PPCT,
            ),
            timetable_source=self._single_active_source(
                owner_id=request.owner_id,
                academic_year=request.academic_year,
                data_type=OperationalDataType.TIMETABLE,
            ),
            academic_week_source=self._single_active_source(
                owner_id=request.owner_id,
                academic_year=request.academic_year,
                data_type=OperationalDataType.ACADEMIC_WEEK,
            ),
        )

    def _single_active_source(
        self,
        *,
        owner_id: str,
        academic_year: str,
        data_type: OperationalDataType,
    ) -> OperationalDataSource | None:
        sources = self._repository.list_sources(
            owner_id=owner_id,
            academic_year=academic_year,
            data_type=data_type,
            status=OperationalDataStatus.ACTIVE,
        )

        if not isinstance(sources, tuple):
            raise TypeError(
                "repository must return tuple"
            )

        if not all(
            isinstance(
                source,
                OperationalDataSource,
            )
            for source in sources
        ):
            raise TypeError(
                "repository returned invalid source"
            )

        if len(sources) > 1:
            raise ValueError(
                "multiple ACTIVE operational data sources "
                f"found for {data_type.value}"
            )

        return sources[0] if sources else None
