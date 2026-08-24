from __future__ import annotations

from dataclasses import dataclass

from educational_planning_v2.adapters.operational_weekly_schedule_workbook_intake import (
    WeeklyScheduleWorkbookIntakeResult,
)
from educational_planning_v2.models.weekly_teaching_schedule import (
    WeeklyTeachingSchedule,
)
from educational_planning_v2.services.weekly_teaching_schedule_service import (
    WeeklyTeachingScheduleService,
)


@dataclass(frozen=True)
class WeeklyScheduleGenerationRequest:
    schedule_id: str
    teacher_id: str
    academic_year: str
    week_number: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schedule_id",
            self._required_text(
                self.schedule_id,
                "schedule_id",
            ),
        )

        object.__setattr__(
            self,
            "teacher_id",
            self._required_text(
                self.teacher_id,
                "teacher_id",
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

        if (
            not isinstance(
                self.week_number,
                int,
            )
            or isinstance(
                self.week_number,
                bool,
            )
            or self.week_number <= 0
        ):
            raise ValueError(
                "week_number must be a positive integer"
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


@dataclass(frozen=True)
class WeeklyScheduleGenerationResult:
    request: WeeklyScheduleGenerationRequest
    schedule: WeeklyTeachingSchedule

    def __post_init__(self) -> None:
        if not isinstance(
            self.request,
            WeeklyScheduleGenerationRequest,
        ):
            raise TypeError(
                "request must be WeeklyScheduleGenerationRequest"
            )

        if not isinstance(
            self.schedule,
            WeeklyTeachingSchedule,
        ):
            raise TypeError(
                "schedule must be WeeklyTeachingSchedule"
            )


class LocalWeeklyScheduleGenerationService:
    """
    Build a weekly teaching schedule from canonical source data
    already produced by workbook intake.

    This service never reads workbook bytes itself.
    """

    def __init__(
        self,
        schedule_service: WeeklyTeachingScheduleService | None = None,
    ) -> None:
        if (
            schedule_service is not None
            and not isinstance(
                schedule_service,
                WeeklyTeachingScheduleService,
            )
        ):
            raise TypeError(
                "schedule_service must be "
                "WeeklyTeachingScheduleService or None"
            )

        self._schedule_service = (
            schedule_service
            or WeeklyTeachingScheduleService()
        )

    def generate(
        self,
        *,
        intake: WeeklyScheduleWorkbookIntakeResult,
        request: WeeklyScheduleGenerationRequest,
    ) -> WeeklyScheduleGenerationResult:
        if not isinstance(
            intake,
            WeeklyScheduleWorkbookIntakeResult,
        ):
            raise TypeError(
                "intake must be WeeklyScheduleWorkbookIntakeResult"
            )

        if not isinstance(
            request,
            WeeklyScheduleGenerationRequest,
        ):
            raise TypeError(
                "request must be WeeklyScheduleGenerationRequest"
            )

        source_data = intake.source_data

        academic_week = source_data.week(
            request.week_number,
            request.academic_year,
        )

        schedule = self._schedule_service.build(
            schedule_id=request.schedule_id,
            teacher_id=request.teacher_id,
            academic_week=academic_week,
            timetable_slots=source_data.timetable_slots,
            curriculum_periods=source_data.curriculum_periods,
            execution_records=source_data.execution_records,
        )

        return WeeklyScheduleGenerationResult(
            request=request,
            schedule=schedule,
        )
