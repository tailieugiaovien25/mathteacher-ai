from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lesson_planning_v2.models.lesson_plan_grouping import LessonPlanGroup, LessonPlanGroupingMode

class CanonicalLessonPlanNamingError(ValueError):
    pass

@dataclass(frozen=True, slots=True)
class CanonicalLessonPlanName:
    basename: str
    filename: str

class CanonicalLessonPlanNamingService:
    def expected_name(self, group: LessonPlanGroup, *, subject_code: str | None = None) -> CanonicalLessonPlanName:
        grade = self._required_grade(group.grade)
        code = self._required_code(subject_code or group.subject_ref)
        first_period = self._first_period(group.curriculum_periods)
        if group.grouping_mode is LessonPlanGroupingMode.BY_WEEK:
            week = self._required_week(group.week_number)
            basename = f"{grade}G{code}{first_period:03d}W{week:02d}"
        else:
            basename = f"{grade}G{code}{first_period:03d}"
        return CanonicalLessonPlanName(basename=basename, filename=basename + ".docx")

    def validate_upload_filename(self, group: LessonPlanGroup, uploaded_filename: str, *, subject_code: str | None = None) -> CanonicalLessonPlanName:
        expected = self.expected_name(group, subject_code=subject_code)
        # Uploaded names can come from either Windows or POSIX clients.  Path
        # only understands the separator of the host running the service, so
        # normalize both separators before comparing the basename.
        actual = str(uploaded_filename or "").replace("\\", "/").rsplit("/", 1)[-1]
        if actual.casefold() != expected.filename.casefold():
            raise CanonicalLessonPlanNamingError(f"LESSON_PLAN_FILENAME_MISMATCH: expected={expected.filename}; actual={actual}")
        return expected

    @staticmethod
    def _required_grade(value):
        if value is None or not 1 <= int(value) <= 12:
            raise CanonicalLessonPlanNamingError("CANONICAL_GRADE_REQUIRED")
        return int(value)

    @staticmethod
    def _required_code(value):
        code = str(value or "").strip().upper()
        if not code or not code.isalnum():
            raise CanonicalLessonPlanNamingError("CANONICAL_SUBJECT_CODE_REQUIRED")
        return code

    @staticmethod
    def _first_period(values: Iterable[object]) -> int:
        periods = []
        for item in tuple(values or ()):
            try:
                value = int(item)
            except (TypeError, ValueError):
                continue
            if value > 0:
                periods.append(value)
        if not periods:
            raise CanonicalLessonPlanNamingError("CURRICULUM_PERIOD_REQUIRED")
        return min(periods)

    @staticmethod
    def _required_week(value):
        if value is None or int(value) < 1:
            raise CanonicalLessonPlanNamingError("WEEK_NUMBER_REQUIRED")
        return int(value)
