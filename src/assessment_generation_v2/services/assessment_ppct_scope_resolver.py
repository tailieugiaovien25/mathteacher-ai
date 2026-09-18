"""Resolve assessment period scope from an already-governed PPCT scope.

This module is deliberately storage-free and UI-free.  It consumes the
same PPCTRow contract already used by educational planning and derives
assessment boundaries from PPCT assessment-marker rows.  No grade- or
period-specific boundary is hard-coded.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from educational_planning_v2.adapters.ppct_plan_item_adapter import (
    PPCTRow,
)


class AssessmentPpctScopeResolutionError(ValueError):
    """Raised when PPCT evidence is insufficient or ambiguous."""


@dataclass(frozen=True, slots=True)
class AssessmentPpctScopeResolution:
    assessment_type: str
    semester: int
    subject_grade: str
    sub_subject: str | None
    period_from: int
    period_to: int
    marker_period: int
    marker_title: str
    marker_row: PPCTRow
    scope_rows: tuple[PPCTRow, ...]

    def __post_init__(self) -> None:
        if self.assessment_type not in {"MIDTERM", "FINAL"}:
            raise AssessmentPpctScopeResolutionError(
                "assessment_type must be MIDTERM or FINAL"
            )

        if self.semester not in {1, 2}:
            raise AssessmentPpctScopeResolutionError(
                "semester must be 1 or 2"
            )

        if self.period_from <= 0:
            raise AssessmentPpctScopeResolutionError(
                "period_from must be positive"
            )

        if self.period_to < self.period_from:
            raise AssessmentPpctScopeResolutionError(
                "period_to must not be before period_from"
            )

        if self.marker_period <= self.period_to:
            raise AssessmentPpctScopeResolutionError(
                "marker_period must be after period_to"
            )


class AssessmentPpctScopeResolver:
    """Derive an assessment scope from one resolved PPCT subject scope."""

    _ASSESSMENT_TYPES = {"MIDTERM", "FINAL"}

    def resolve(
        self,
        *,
        rows: tuple[PPCTRow, ...],
        assessment_type: str,
        semester: int,
    ) -> AssessmentPpctScopeResolution:
        normalized_type = self._normalize_assessment_type(
            assessment_type
        )
        normalized_semester = self._normalize_semester(
            semester
        )

        self._validate_rows(rows)

        subject_grade = rows[0].subject_grade.strip()
        sub_subject = self._optional_text(
            rows[0].sub_subject
        )

        target_marker_groups = self._marker_groups(
            rows=rows,
            marker_key=(
                normalized_type,
                normalized_semester,
            ),
        )

        if not target_marker_groups:
            raise AssessmentPpctScopeResolutionError(
                "PPCT assessment marker not found for "
                f"{normalized_type} semester {normalized_semester}"
            )

        if len(target_marker_groups) != 1:
            raise AssessmentPpctScopeResolutionError(
                "PPCT assessment marker is ambiguous for "
                f"{normalized_type} semester {normalized_semester}"
            )

        target_marker_group = target_marker_groups[0]
        marker = target_marker_group[0]

        lower_exclusive = 0

        if normalized_semester == 2:
            prior_final_groups = self._marker_groups(
                rows=rows,
                marker_key=("FINAL", 1),
            )

            if not prior_final_groups:
                raise AssessmentPpctScopeResolutionError(
                    "semester 2 scope cannot be derived because "
                    "FINAL semester 1 marker is missing"
                )

            if len(prior_final_groups) != 1:
                raise AssessmentPpctScopeResolutionError(
                    "semester 2 scope cannot be derived because "
                    "FINAL semester 1 marker is ambiguous"
                )

            prior_final_group = prior_final_groups[0]
            prior_final_end_period = max(
                int(row.period)
                for row in prior_final_group
            )

            if prior_final_end_period >= int(marker.period):
                raise AssessmentPpctScopeResolutionError(
                    "semester 1 final marker must precede "
                    "the semester 2 assessment marker"
                )

            lower_exclusive = prior_final_end_period

        scope_rows = tuple(
            sorted(
                (
                    row
                    for row in rows
                    if lower_exclusive
                    < int(row.period)
                    < int(marker.period)
                ),
                key=lambda row: int(row.period),
            )
        )

        if not scope_rows:
            raise AssessmentPpctScopeResolutionError(
                "PPCT contains no periods before the assessment marker"
            )

        period_numbers = tuple(
            int(row.period)
            for row in scope_rows
        )

        return AssessmentPpctScopeResolution(
            assessment_type=normalized_type,
            semester=normalized_semester,
            subject_grade=subject_grade,
            sub_subject=sub_subject,
            period_from=min(period_numbers),
            period_to=max(period_numbers),
            marker_period=int(marker.period),
            marker_title=marker.lesson_name.strip(),
            marker_row=marker,
            scope_rows=scope_rows,
        )

    @classmethod
    def _validate_rows(
        cls,
        rows: tuple[PPCTRow, ...],
    ) -> None:
        if not isinstance(rows, tuple):
            raise TypeError("rows must be a tuple")

        if not rows:
            raise AssessmentPpctScopeResolutionError(
                "PPCT scope rows must not be empty"
            )

        if not all(
            isinstance(row, PPCTRow)
            for row in rows
        ):
            raise TypeError(
                "rows must contain PPCTRow values"
            )

        first_subject = cls._fold(
            rows[0].subject_grade
        )
        first_sub_subject = cls._fold_optional(
            rows[0].sub_subject
        )

        for row in rows:
            if int(row.period) <= 0:
                raise AssessmentPpctScopeResolutionError(
                    "PPCT period must be positive"
                )

            if cls._fold(row.subject_grade) != first_subject:
                raise AssessmentPpctScopeResolutionError(
                    "rows contain more than one PPCT subject-grade scope"
                )

            if (
                cls._fold_optional(row.sub_subject)
                != first_sub_subject
            ):
                raise AssessmentPpctScopeResolutionError(
                    "rows contain more than one PPCT sub-subject scope"
                )

    @classmethod
    def _marker_groups(
        cls,
        *,
        rows: tuple[PPCTRow, ...],
        marker_key: tuple[str, int],
    ) -> tuple[tuple[PPCTRow, ...], ...]:
        matching_rows = tuple(
            sorted(
                (
                    row
                    for row in rows
                    if cls._marker_key(row.lesson_name)
                    == marker_key
                ),
                key=lambda row: (
                    int(row.period),
                    cls._fold(row.lesson_name),
                ),
            )
        )

        if not matching_rows:
            return ()

        groups: list[list[PPCTRow]] = []
        current_group: list[PPCTRow] = []
        current_title: str | None = None
        previous_period: int | None = None

        for row in matching_rows:
            period = int(row.period)
            title = cls._fold(row.lesson_name)

            same_logical_span = (
                bool(current_group)
                and current_title == title
                and previous_period is not None
                and period <= previous_period + 1
            )

            if not current_group or same_logical_span:
                current_group.append(row)
            else:
                groups.append(current_group)
                current_group = [row]

            current_title = title
            if previous_period is None or not same_logical_span:
                previous_period = period
            else:
                previous_period = max(
                    previous_period,
                    period,
                )

        if current_group:
            groups.append(current_group)

        return tuple(
            tuple(group)
            for group in groups
        )

    @classmethod
    def _marker_key(
        cls,
        lesson_name: str,
    ) -> tuple[str, int] | None:
        text = cls._fold(lesson_name)

        if "kiem tra" not in text:
            return None

        semester = cls._semester_from_text(text)

        if semester is None:
            return None

        tokens = set(
            re.findall(r"[a-z0-9]+", text)
        )

        if "giua" in tokens:
            return "MIDTERM", semester

        if (
            "cuoi" in tokens
            or "hoc ky" in text
            or "hoc ki" in text
        ):
            return "FINAL", semester

        return None

    @staticmethod
    def _semester_from_text(
        text: str,
    ) -> int | None:
        semester_2_patterns = (
            r"\bhk\s*2\b",
            r"\bhoc\s+k[yi]\s*(?:ii|2)\b",
            r"\bk[yi]\s*(?:ii|2)\b",
        )
        semester_1_patterns = (
            r"\bhk\s*1\b",
            r"\bhoc\s+k[yi]\s*(?:i|1)\b",
            r"\bk[yi]\s*(?:i|1)\b",
        )

        if any(
            re.search(pattern, text)
            for pattern in semester_2_patterns
        ):
            return 2

        if any(
            re.search(pattern, text)
            for pattern in semester_1_patterns
        ):
            return 1

        return None

    @classmethod
    def _normalize_assessment_type(
        cls,
        value: object,
    ) -> str:
        normalized = str(value or "").strip().upper()

        if normalized not in cls._ASSESSMENT_TYPES:
            raise AssessmentPpctScopeResolutionError(
                "assessment_type must be MIDTERM or FINAL"
            )

        return normalized

    @staticmethod
    def _normalize_semester(
        value: object,
    ) -> int:
        if isinstance(value, bool):
            raise AssessmentPpctScopeResolutionError(
                "semester must be 1 or 2"
            )

        try:
            normalized = int(value)
        except (TypeError, ValueError) as error:
            raise AssessmentPpctScopeResolutionError(
                "semester must be 1 or 2"
            ) from error

        if normalized not in {1, 2}:
            raise AssessmentPpctScopeResolutionError(
                "semester must be 1 or 2"
            )

        return normalized

    @staticmethod
    def _optional_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        text = value.strip()

        return text or None

    @staticmethod
    def _fold_optional(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = AssessmentPpctScopeResolver._fold(
            value
        )

        return normalized or None

    @staticmethod
    def _fold(
        value: object,
    ) -> str:
        text = str(value or "").strip().casefold()
        text = unicodedata.normalize(
            "NFD",
            text,
        )
        text = "".join(
            character
            for character in text
            if unicodedata.category(character) != "Mn"
        )
        text = text.replace("đ", "d")

        return " ".join(text.split())