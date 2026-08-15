from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.exporters.weekly_schedule_excel_exporter import (
    WeeklyScheduleExcelExport,
    WeeklyScheduleExcelExporter,
)
from educational_planning_v2.services.local_weekly_schedule_generation_service import (
    WeeklyScheduleGenerationResult,
)


@dataclass(frozen=True)
class WeeklyScheduleOutputResult:
    generation: WeeklyScheduleGenerationResult
    artifact: WeeklyScheduleExcelExport

    def __post_init__(self) -> None:
        if not isinstance(
            self.generation,
            WeeklyScheduleGenerationResult,
        ):
            raise TypeError(
                "generation must be WeeklyScheduleGenerationResult"
            )

        if not isinstance(
            self.artifact,
            WeeklyScheduleExcelExport,
        ):
            raise TypeError(
                "artifact must be WeeklyScheduleExcelExport"
            )


class WeeklyScheduleOutputService:
    """
    Convert a generated canonical weekly teaching schedule into
    a downloadable output artifact.

    This service delegates workbook rendering to the existing
    WeeklyScheduleExcelExporter.

    It owns no physical file writing and no delivery destination.
    """

    def __init__(
        self,
        exporter: WeeklyScheduleExcelExporter | None = None,
    ) -> None:
        if (
            exporter is not None
            and not isinstance(
                exporter,
                WeeklyScheduleExcelExporter,
            )
        ):
            raise TypeError(
                "exporter must be WeeklyScheduleExcelExporter or None"
            )

        self._exporter = (
            exporter
            or WeeklyScheduleExcelExporter()
        )

    def export_excel(
        self,
        *,
        generation: WeeklyScheduleGenerationResult,
    ) -> WeeklyScheduleOutputResult:
        if not isinstance(
            generation,
            WeeklyScheduleGenerationResult,
        ):
            raise TypeError(
                "generation must be WeeklyScheduleGenerationResult"
            )

        artifact = self._exporter.export(
            generation.schedule
        )

        if not isinstance(
            artifact,
            WeeklyScheduleExcelExport,
        ):
            raise TypeError(
                "exporter must return WeeklyScheduleExcelExport"
            )

        return WeeklyScheduleOutputResult(
            generation=generation,
            artifact=artifact,
        )
