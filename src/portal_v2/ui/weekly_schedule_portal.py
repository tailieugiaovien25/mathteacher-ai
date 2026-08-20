from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from educational_planning_v2.models import (
    TeachingSession,
)
from educational_planning_v2.services.weekly_schedule_output_service import (
    WeeklyScheduleOutputResult,
)


class WeeklySchedulePortalSource(str, Enum):
    LOCAL_UPLOAD = "LOCAL_UPLOAD"
    SYSTEM_LIBRARY = "SYSTEM_LIBRARY"


@dataclass(frozen=True)
class WeeklySchedulePortalPreviewRow:
    teaching_date: date
    weekday: int
    timetable_period: int
    session: TeachingSession
    class_id: str
    subject_ref: str
    component_ref: str | None
    curriculum_period: int
    lesson_id: str
    lesson_title: str
    period_in_lesson: int
    teaching_equipment: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.teaching_date, date):
            raise TypeError("teaching_date must be date")

        if not isinstance(
            self.session,
            TeachingSession,
        ):
            raise TypeError(
                "session must be TeachingSession"
            )

        for name in (
            "weekday",
            "timetable_period",
            "curriculum_period",
            "period_in_lesson",
        ):
            value = getattr(self, name)

            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value <= 0
            ):
                raise ValueError(
                    f"{name} must be a positive integer"
                )

        for name in (
            "class_id",
            "subject_ref",
            "lesson_id",
            "lesson_title",
        ):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{name} must not be empty"
                )

            object.__setattr__(
                self,
                name,
                normalized,
            )

        if self.component_ref is not None:
            if not isinstance(
                self.component_ref,
                str,
            ):
                raise TypeError(
                    "component_ref must be str or None"
                )

            normalized_component = (
                self.component_ref.strip()
            )

            object.__setattr__(
                self,
                "component_ref",
                normalized_component or None,
            )

        if not isinstance(
            self.teaching_equipment,
            tuple,
        ):
            raise TypeError(
                "teaching_equipment must be tuple"
            )


@dataclass(frozen=True)
class WeeklySchedulePortalDownload:
    file_name: str
    content: bytes
    mime_type: str

    def __post_init__(self) -> None:
        for name in (
            "file_name",
            "mime_type",
        ):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{name} must not be empty"
                )

            object.__setattr__(
                self,
                name,
                normalized,
            )

        if not isinstance(
            self.content,
            bytes,
        ):
            raise TypeError(
                "content must be bytes"
            )

        if not self.content:
            raise ValueError(
                "content must not be empty"
            )


@dataclass(frozen=True)
class WeeklySchedulePortalViewModel:
    schedule_id: str
    teacher_id: str
    academic_year: str
    week_number: int
    rows: tuple[WeeklySchedulePortalPreviewRow, ...]
    download: WeeklySchedulePortalDownload

    def __post_init__(self) -> None:
        for name in (
            "schedule_id",
            "teacher_id",
            "academic_year",
        ):
            value = getattr(self, name)

            if not isinstance(value, str):
                raise TypeError(
                    f"{name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{name} must not be empty"
                )

            object.__setattr__(
                self,
                name,
                normalized,
            )

        if (
            not isinstance(self.week_number, int)
            or isinstance(self.week_number, bool)
            or self.week_number <= 0
        ):
            raise ValueError(
                "week_number must be a positive integer"
            )

        if not isinstance(self.rows, tuple):
            raise TypeError(
                "rows must be tuple"
            )

        if not all(
            isinstance(
                row,
                WeeklySchedulePortalPreviewRow,
            )
            for row in self.rows
        ):
            raise TypeError(
                "rows contain invalid value"
            )

        if not isinstance(
            self.download,
            WeeklySchedulePortalDownload,
        ):
            raise TypeError(
                "download must be WeeklySchedulePortalDownload"
            )


class WeeklySchedulePortalPresenter:
    """
    Convert application output into a UI-safe view model.

    No Streamlit, spreadsheet rendering, storage, or schedule
    generation responsibility belongs here.
    """

    def present(
        self,
        *,
        output: WeeklyScheduleOutputResult,
    ) -> WeeklySchedulePortalViewModel:
        if not isinstance(
            output,
            WeeklyScheduleOutputResult,
        ):
            raise TypeError(
                "output must be WeeklyScheduleOutputResult"
            )

        schedule = output.generation.schedule

        rows = tuple(
            WeeklySchedulePortalPreviewRow(
                teaching_date=entry.teaching_date,
                weekday=entry.weekday,
                timetable_period=entry.timetable_period,
                session=entry.session,
                class_id=entry.class_id,
                subject_ref=entry.subject_ref,
                component_ref=entry.component_ref,
                curriculum_period=entry.curriculum_period,
                lesson_id=entry.lesson_id,
                lesson_title=entry.lesson_title,
                period_in_lesson=entry.period_in_lesson,
                teaching_equipment=entry.teaching_equipment,
            )
            for entry in schedule.entries
        )

        artifact = output.artifact

        download = WeeklySchedulePortalDownload(
            file_name=artifact.file_name,
            content=artifact.content,
            mime_type=artifact.mime_type,
        )

        return WeeklySchedulePortalViewModel(
            schedule_id=schedule.schedule_id,
            teacher_id=schedule.teacher_id,
            academic_year=(
                schedule.academic_week.academic_year
            ),
            week_number=(
                schedule.academic_week.week_number
            ),
            rows=rows,
            download=download,
        )
