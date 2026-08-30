from __future__ import annotations

from collections.abc import Iterable, Mapping, Callable
from hashlib import sha256
from typing import Any

from lesson_planning_v2.models.lesson_plan_grouping import (
    LessonPlanGroupValidationError,
    LessonPlanGroup,
    LessonPlanGroupingMode,
    LessonPlanGroupingPolicy,
    TeachingOccurrence,
)


class LessonPlanGroupingPolicyResolver:
    def __init__(
        self,
        policies: Iterable[LessonPlanGroupingPolicy] = (),
        *,
        default_mode: LessonPlanGroupingMode = LessonPlanGroupingMode.BY_PERIOD,
    ) -> None:
        self._policies = {
            (
                str(item.subject_ref or "").strip(),
                str(item.component_ref or "").strip(),
            ): item.mode
            for item in policies
        }
        self._default_mode = default_mode

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[tuple[str, str], LessonPlanGroupingMode | str],
        *,
        default_mode: LessonPlanGroupingMode = LessonPlanGroupingMode.BY_PERIOD,
    ) -> "LessonPlanGroupingPolicyResolver":
        policies = tuple(
            LessonPlanGroupingPolicy(
                subject_ref=subject_ref,
                component_ref=component_ref,
                mode=(
                    mode
                    if isinstance(mode, LessonPlanGroupingMode)
                    else LessonPlanGroupingMode(str(mode))
                ),
            )
            for (subject_ref, component_ref), mode in mapping.items()
        )
        return cls(policies, default_mode=default_mode)

    def resolve(self, *, subject_ref: str, component_ref: str) -> LessonPlanGroupingMode:
        subject = str(subject_ref or "").strip()
        component = str(component_ref or "").strip()
        return (
            self._policies.get((subject, component))
            or self._policies.get((subject, ""))
            or self._default_mode
        )


class LessonPlanGroupingService:
    def group(
        self,
        rows: Iterable[object],
        *,
        policy_resolver: LessonPlanGroupingPolicyResolver,
        grade_resolver: Callable[[object], int | None] | None = None,
    ) -> tuple[LessonPlanGroup, ...]:
        grouped: dict[tuple[Any, ...], list[tuple[int, object, int | None]]] = {}

        for row_index, row in enumerate(tuple(rows)):
            subject_ref = self._text(row, "subject_ref")
            component_ref = self._text(row, "component_ref")
            grade = grade_resolver(row) if grade_resolver else self._grade(row)
            grade = self._require_grade(grade, row_index=row_index)
            mode = policy_resolver.resolve(
                subject_ref=subject_ref,
                component_ref=component_ref,
            )

            if mode is LessonPlanGroupingMode.BY_PERIOD:
                key = (
                    mode.value,
                    subject_ref,
                    component_ref,
                    grade,
                    getattr(row, "curriculum_period", None),
                )
            elif mode is LessonPlanGroupingMode.BY_GRADE:
                key = (
                    mode.value,
                    subject_ref,
                    component_ref,
                    grade,
                )
            elif mode is LessonPlanGroupingMode.BY_WEEK:
                academic_year = self._text(row, "academic_year")
                week_number = getattr(row, "week_number", None)
                if not academic_year or week_number is None:
                    raise LessonPlanGroupValidationError(
                        "BY_WEEK_REQUIRES_ACADEMIC_YEAR_AND_WEEK"
                    )
                key = (
                    mode.value,
                    academic_year,
                    int(week_number),
                    subject_ref,
                    component_ref,
                    grade,
                )
            else:
                key = (
                    mode.value,
                    subject_ref,
                    component_ref,
                    grade,
                    self._lesson_identity(row),
                )

            grouped.setdefault(key, []).append((row_index, row, grade))

        result = []
        for key, members in grouped.items():
            first_index, first_row, grade = members[0]
            mode = LessonPlanGroupingMode(key[0])

            periods = tuple(dict.fromkeys(
                getattr(row, "curriculum_period", None)
                for _, row, _ in members
                if getattr(row, "curriculum_period", None) is not None
            ))
            occurrences = tuple(
                TeachingOccurrence(
                    row_index=row_index,
                    class_id=self._text(row, "class_id"),
                    teaching_date=getattr(row, "teaching_date", None),
                    timetable_period=getattr(row, "timetable_period", None),
                    timetable_slot_id=self._text(row, "timetable_slot_id") or None,
                    curriculum_period=getattr(row, "curriculum_period", None),
                )
                for row_index, row, _ in members
            )

            lesson_id = self._text(first_row, "lesson_id") or None
            lesson_title = self._text(first_row, "lesson_title")
            result.append(
                LessonPlanGroup(
                    group_id=self._group_id(
                        mode=mode,
                        subject_ref=self._text(first_row, "subject_ref"),
                        component_ref=self._text(first_row, "component_ref"),
                        grade=grade,
                        lesson_id=lesson_id,
                        lesson_title=lesson_title,
                        curriculum_periods=periods,
                    ),
                    grouping_mode=mode,
                    subject_ref=self._text(first_row, "subject_ref"),
                    component_ref=self._text(first_row, "component_ref"),
                    grade=grade,
                    lesson_id=lesson_id,
                    lesson_title=lesson_title,
                    curriculum_periods=periods,
                    occurrences=occurrences,
                    representative_row_index=first_index,
                )
            )

        return tuple(result)

    @staticmethod
    def _require_grade(grade: int | None, *, row_index: int) -> int:
        if grade is None:
            raise LessonPlanGroupValidationError(
                f"CANONICAL_GRADE_REQUIRED: row_index={row_index}"
            )
        value = int(grade)
        if not 1 <= value <= 12:
            raise LessonPlanGroupValidationError(
                f"INVALID_CANONICAL_GRADE: row_index={row_index}, grade={grade}"
            )
        return value

    @staticmethod
    def _text(row: object, field: str) -> str:
        return str(getattr(row, field, "") or "").strip()

    @staticmethod
    def _grade(row: object) -> int | None:
        raw = getattr(row, "grade", None)
        if raw is None:
            raw = getattr(row, "grade_level", None)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        return value if 1 <= value <= 12 else None

    def _lesson_identity(self, row: object) -> tuple[str, str]:
        lesson_id = self._text(row, "lesson_id")
        if lesson_id:
            return ("lesson_id", lesson_id)

        lesson_group_id = self._text(row, "lesson_group_id")
        if lesson_group_id:
            return ("lesson_group_id", lesson_group_id)

        return ("provisional_title", self._text(row, "lesson_title").casefold())

    @staticmethod
    def _group_id(
        *,
        mode: LessonPlanGroupingMode,
        subject_ref: str,
        component_ref: str,
        grade: int | None,
        lesson_id: str | None,
        lesson_title: str,
        curriculum_periods: tuple,
    ) -> str:
        payload = "|".join(
            (
                mode.value,
                subject_ref,
                component_ref,
                str(grade or ""),
                str(lesson_id or ""),
                lesson_title.casefold(),
                ",".join(str(item) for item in curriculum_periods),
            )
        )
        return "lpg_" + sha256(payload.encode("utf-8")).hexdigest()[:20]
