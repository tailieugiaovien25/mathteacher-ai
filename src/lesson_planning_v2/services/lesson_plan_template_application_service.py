from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from lesson_planning_v2.lesson_plan_template_profile import (
    DraftingWeekday,
    LessonPlanAlignment,
    LessonPlanTemplateProfile,
)


_WEEKDAY_INDEX = {
    DraftingWeekday.THURSDAY: 3,
    DraftingWeekday.FRIDAY: 4,
    DraftingWeekday.SATURDAY: 5,
    DraftingWeekday.SUNDAY: 6,
}


@dataclass(frozen=True)
class LessonTeachingOccurrence:
    """
    One teaching date for one class.

    projected=True means the date was inferred from the
    current timetable because a confirmed future timetable
    was not yet available.
    """

    class_name: str
    teaching_date: date
    projected: bool = False

    def __post_init__(self) -> None:
        if not self.class_name.strip():
            raise ValueError(
                "class_name must not be blank"
            )


@dataclass(frozen=True)
class LessonPlanTemplateApplicationResult:
    drafting_date: date
    approval_date: date

    teaching_occurrences: tuple[
        LessonTeachingOccurrence,
        ...
    ]

    curriculum_periods: tuple[int, ...]

    period_heading: str
    lesson_title: str

    metadata_alignment: LessonPlanAlignment
    period_alignment: LessonPlanAlignment
    period_bold: bool

    lesson_title_alignment: LessonPlanAlignment
    lesson_title_bold: bool

    approval_alignment: LessonPlanAlignment
    approval_label: str
    approval_signature_blank_lines: int


class LessonPlanTemplateApplicationService:
    """
    Resolve lesson-plan metadata from a template profile.

    Responsibilities:
    - resolve one drafting date for the teaching week;
    - resolve the approval date;
    - preserve all teaching dates by class, including dates
      that fall in the following week;
    - produce one period heading for the whole lesson;
    - apply title casing rules from the selected template.

    This service does not modify DOCX files.
    """

    def apply(
        self,
        *,
        profile: LessonPlanTemplateProfile,
        week_start_date: date,
        curriculum_periods: tuple[int, ...],
        lesson_title: str,
        teaching_occurrences: tuple[
            LessonTeachingOccurrence,
            ...
        ],
    ) -> LessonPlanTemplateApplicationResult:
        self._validate_week_start(
            week_start_date
        )

        normalized_periods = (
            self._normalize_periods(
                curriculum_periods
            )
        )

        normalized_title = (
            self._normalize_lesson_title(
                lesson_title,
                uppercase=(
                    profile.header
                    .lesson_title_uppercase
                ),
            )
        )

        normalized_occurrences = (
            self._normalize_occurrences(
                teaching_occurrences
            )
        )

        drafting_date = (
            self._resolve_drafting_date(
                profile=profile,
                week_start_date=(
                    week_start_date
                ),
            )
        )

        approval_date = (
            drafting_date
            + timedelta(
                days=(
                    profile.scheduling
                    .approval_offset_days
                )
            )
        )

        return (
            LessonPlanTemplateApplicationResult(
                drafting_date=drafting_date,
                approval_date=approval_date,
                teaching_occurrences=(
                    normalized_occurrences
                ),
                curriculum_periods=(
                    normalized_periods
                ),
                period_heading=(
                    self._build_period_heading(
                        normalized_periods
                    )
                ),
                lesson_title=normalized_title,
                metadata_alignment=(
                    profile.header
                    .drafting_teaching_alignment
                ),
                period_alignment=(
                    profile.header
                    .period_alignment
                ),
                period_bold=(
                    profile.header.period_bold
                ),
                lesson_title_alignment=(
                    profile.header
                    .lesson_title_alignment
                ),
                lesson_title_bold=(
                    profile.header
                    .lesson_title_bold
                ),
                approval_alignment=(
                    profile.approval.alignment
                ),
                approval_label=(
                    profile.approval
                    .approval_label
                ),
                approval_signature_blank_lines=(
                    profile.approval
                    .signature_blank_lines
                ),
            )
        )

    @staticmethod
    def _validate_week_start(
        week_start_date: date,
    ) -> None:
        if week_start_date.weekday() != 0:
            raise ValueError(
                "week_start_date must be Monday"
            )

    @staticmethod
    def _resolve_drafting_date(
        *,
        profile: LessonPlanTemplateProfile,
        week_start_date: date,
    ) -> date:
        previous_monday = (
            week_start_date
            - timedelta(days=7)
        )

        weekday_index = _WEEKDAY_INDEX[
            profile.scheduling
            .drafting_weekday
        ]

        return (
            previous_monday
            + timedelta(
                days=weekday_index
            )
        )

    @staticmethod
    def _normalize_periods(
        curriculum_periods: tuple[int, ...],
    ) -> tuple[int, ...]:
        if not curriculum_periods:
            raise ValueError(
                "curriculum_periods must not be empty"
            )

        if any(
            period <= 0
            for period in curriculum_periods
        ):
            raise ValueError(
                "curriculum periods must be positive"
            )

        return tuple(
            sorted(
                dict.fromkeys(
                    curriculum_periods
                )
            )
        )

    @staticmethod
    def _build_period_heading(
        curriculum_periods: tuple[int, ...],
    ) -> str:
        values = " + ".join(
            str(period)
            for period in curriculum_periods
        )

        return (
            "\u0054\u0049\u1ebe\u0054 "
            + values
        )

    @staticmethod
    def _normalize_lesson_title(
        lesson_title: str,
        *,
        uppercase: bool,
    ) -> str:
        value = lesson_title.strip()

        if not value:
            raise ValueError(
                "lesson_title must not be blank"
            )

        if uppercase:
            return value.upper()

        return value

    @staticmethod
    def _normalize_occurrences(
        teaching_occurrences: tuple[
            LessonTeachingOccurrence,
            ...
        ],
    ) -> tuple[
        LessonTeachingOccurrence,
        ...
    ]:
        if not teaching_occurrences:
            raise ValueError(
                "teaching_occurrences "
                "must not be empty"
            )

        return tuple(
            sorted(
                teaching_occurrences,
                key=lambda item: (
                    item.teaching_date,
                    item.class_name,
                ),
            )
        )
